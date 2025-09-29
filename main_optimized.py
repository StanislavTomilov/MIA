"""
Оптимизированная версия main.py
"""
import os
import time
import threading
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from pynput import keyboard as kb

from utils.config import get_config
from utils.app_state import state_manager
from utils.audio_manager import AudioManager, AudioRecordingError
from utils.model_cache import model_cache

from transcriber.whisper_optimized import OptimizedWhisperTranscriber, TranscriptionError
from llms.llm import LocalLLMClient
from prompts.templates import get_corporate_summary_prompt, get_interview_prompt

from rag.embedder import Embedder
from rag.search import search
from prompts.templates import get_rag_answer_prompt
import faiss
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mia.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MIAApplication:
    """Основной класс приложения MIA"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audio_manager: Optional[AudioManager] = None
        self.transcriber: Optional[OptimizedWhisperTranscriber] = None
        self.llm_client: Optional[LocalLLMClient] = None
        self.embedder: Optional[Embedder] = None
        
        # Флаг для graceful shutdown
        self.running = True
        
        # Инициализация компонентов
        self._initialize_components()
        
        # Обработчики сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_components(self):
        """Инициализация всех компонентов приложения"""
        try:
            logger.info("Initializing MIA application...")
            
            # Инициализация аудио менеджера
            self.audio_manager = AudioManager(self.config)
            self.audio_manager.setup_virtual_cable()
            
            # Инициализация транскрайбера
            self.transcriber = OptimizedWhisperTranscriber(self.config)
            
            # Инициализация LLM клиента
            self.llm_client = LocalLLMClient(
                host=self.config["llm_host"],
                model=self.config["llm_model"]
            )
            
            # Инициализация эмбеддера
            self.embedder = Embedder(
                model_name=self.config["rag_model_name"],
                device=self.config["asr_device"]
            )
            
            logger.info("MIA application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Очистка ресурсов"""
        logger.info("Cleaning up resources...")
        
        if self.audio_manager:
            self.audio_manager.cleanup()
        
        # Очистка кэша моделей
        model_cache.clear()
    
    def handle_meeting_recording(self):
        """Обработка записи встречи"""
        try:
            if not state_manager.is_meeting_active():
                # Старт записи
                self.audio_manager.start_main_recording()
                state_manager.set_meeting_active(True)
                logger.info("Meeting recording started")
                print("▶️ Основная запись встречи начата (Ctrl+R чтобы остановить)")
            else:
                # Остановка записи
                audio_path = self.audio_manager.stop_main_recording()
                state_manager.set_meeting_active(False)
                logger.info("Meeting recording stopped")
                print("⏹ Основная запись завершена. Обработка...")
                
                # Транскрипция
                transcript_text = self.transcriber.transcribe(audio_path)
                
                # Генерация саммари
                prompt = get_corporate_summary_prompt(transcript_text)
                summary_json_str = self.llm_client.generate_answer(prompt)
                
                # Сохранение саммари
                self._save_summary(audio_path, summary_json_str)
                
        except (AudioRecordingError, TranscriptionError) as e:
            logger.error(f"Meeting recording error: {e}")
            print(f"❌ Ошибка записи встречи: {e}")
            state_manager.set_meeting_active(False)
        except Exception as e:
            logger.error(f"Unexpected error in meeting recording: {e}")
            print(f"❌ Неожиданная ошибка: {e}")
            state_manager.set_meeting_active(False)
    
    def handle_question_recording(self):
        """Обработка записи вопроса"""
        try:
            if not state_manager.is_question_active():
                # Проверка, что встреча активна
                if not state_manager.is_meeting_active():
                    print("❌ Ошибка: Основная запись не идёт. Нельзя стартовать вопрос.")
                    return
                
                # Старт записи вопроса
                self.audio_manager.start_question_recording()
                state_manager.set_question_active(True)
                logger.info("Question recording started")
                print("🔴 Запись вопроса начата (Ctrl+Q чтобы остановить)")
            else:
                # Остановка записи вопроса
                audio_path = self.audio_manager.stop_question_recording()
                state_manager.set_question_active(False)
                logger.info("Question recording stopped")
                print("🔵 Запись вопроса завершена. Обработка...")
                
                # Транскрипция
                question_text = self.transcriber.transcribe(audio_path)
                print(f"Вопрос: {question_text}")
                
                # Генерация ответа
                prompt = get_interview_prompt(question_text)
                
                # Потоковая генерация
                start_time = time.perf_counter()
                for chunk in self.llm_client.generate_answer_stream(prompt):
                    print(chunk, end='', flush=True)
                print()
                
                elapsed = time.perf_counter() - start_time
                print(f"⏱️ Ответ сгенерирован за {elapsed:.2f} сек.")
                
        except (AudioRecordingError, TranscriptionError) as e:
            logger.error(f"Question recording error: {e}")
            print(f"❌ Ошибка записи вопроса: {e}")
            state_manager.set_question_active(False)
        except Exception as e:
            logger.error(f"Unexpected error in question recording: {e}")
            print(f"❌ Неожиданная ошибка: {e}")
            state_manager.set_question_active(False)
    
    def _save_summary(self, audio_path: str, summary_json_str: str):
        """Сохранение саммари"""
        try:
            summaries_dir = Path(self.config["summaries_dir"])
            summaries_dir.mkdir(exist_ok=True)
            
            base = Path(audio_path).stem
            out_path = summaries_dir / f"{base}_summary.json"
            
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(summary_json_str)
            
            logger.info(f"Summary saved: {out_path}")
            print(f"✅ Саммари встречи сохранено: {out_path}")
            
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            print(f"❌ Ошибка сохранения саммари: {e}")
    
    def run_rag_chat_summaries(self):
        """RAG чат по саммари"""
        try:
            # Загрузка индекса
            idx_path = Path(self.config["rag_store_dir"]) / "faiss.index"
            meta_path = Path(self.config["rag_store_dir"]) / "meta.json"
            
            if not (idx_path.exists() and meta_path.exists()):
                print("[RAG] Индекс по саммари не найден. Сначала: python -m rag.build")
                return
            
            index = faiss.read_index(str(idx_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                metas = json.load(f)
            
            print("\n[RAG] Чат по САММАРИ. Введите вопрос (или 'exit'):")
            
            while self.running:
                try:
                    q = input("?> ").strip()
                    if not q:
                        continue
                    if q.lower() in ("exit", "quit"):
                        print("[RAG] Выход.")
                        break
                    
                    # Поиск
                    q_vec = self.embedder.encode([q])
                    hits = search(index, metas, q_vec, 
                                top_k=self.config["rag_top_k"], 
                                threshold=self.config["rag_threshold"])
                    
                    # Формирование ответа
                    lines = []
                    for h in hits:
                        p = h["meta"].get("path")
                        doc_id = h["meta"].get("doc_id")
                        chunk_id = h["meta"].get("chunk_id")
                        lines.append(f"[summary:{doc_id}#chunk{chunk_id}] score={h['score']:.2f} | {p}")
                    
                    retrieved = "Найдены фрагменты саммари:\n" + ("\n".join(lines) if lines else "ничего не найдено")
                    prompt = get_rag_answer_prompt(q, retrieved)
                    
                    # Генерация ответа
                    print("\n--- Ответ (stream) ---")
                    for chunk in self.llm_client.generate_answer_stream(prompt):
                        print(chunk, end="", flush=True)
                    print("\n----------------------\n")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"RAG chat error: {e}")
                    print(f"❌ Ошибка RAG чата: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to start RAG chat: {e}")
            print(f"❌ Ошибка запуска RAG чата: {e}")
    
    def on_press(self, key):
        """Обработчик нажатия клавиш"""
        state_manager.add_pressed_key(key)
        
        # Ctrl+R — старт/стоп встречи
        if state_manager.has_key_combination([kb.Key.ctrl_l, kb.Key.ctrl_r], ['r', 'R']):
            threading.Thread(target=self.handle_meeting_recording, daemon=True).start()
        
        # Ctrl+Q — старт/стоп вопроса
        if state_manager.has_key_combination([kb.Key.ctrl_l, kb.Key.ctrl_r], ['q', 'Q']):
            threading.Thread(target=self.handle_question_recording, daemon=True).start()
        
        # ESC — выход
        if key == kb.Key.esc:
            logger.info("ESC pressed, exiting...")
            self.running = False
            return False
    
    def on_release(self, key):
        """Обработчик отпускания клавиш"""
        state_manager.remove_pressed_key(key)
    
    def run(self):
        """Запуск приложения"""
        try:
            print("====================================")
            print("Ctrl+R — старт/стоп записи всей встречи")
            print("Ctrl+Q — старт/стоп записи вопроса")
            print("ESC    — выход")
            print("====================================")
            
            # Запуск слушателя клавиш
            with kb.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                listener.join()
            
            # RAG чат после выхода из основного цикла
            if self.running:
                self.run_rag_chat_summaries()
                
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"❌ Ошибка приложения: {e}")
        finally:
            self.cleanup()


def main():
    """Точка входа"""
    try:
        # Получение конфигурации
        config = get_config()
        
        # Создание и запуск приложения
        app = MIAApplication(config)
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"❌ Ошибка запуска приложения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

