"""
Оптимизированная транскрипция с кэшированием
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import time

from faster_whisper import WhisperModel
from utils.config import get_config
from utils.model_cache import cached_model, get_asr_cache_key

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Исключение для ошибок транскрипции"""
    pass


class OptimizedWhisperTranscriber:
    """Оптимизированный транскрайбер с кэшированием"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.transcripts_dir = Path(config["transcripts_dir"])
        self.meetings_dir = self.transcripts_dir / "meetings"
        self.questions_dir = self.transcripts_dir / "questions"
        
        # Создание директорий
        self.meetings_dir.mkdir(parents=True, exist_ok=True)
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        
        # Кэшированная модель
        self._model: Optional[WhisperModel] = None
    
    @cached_model(get_asr_cache_key)
    def _load_model(self, model_size: str, device: str, compute_type: str) -> WhisperModel:
        """Загрузка модели с кэшированием"""
        logger.info(f"Loading Faster-Whisper model: {model_size} on {device}")
        start_time = time.time()
        
        try:
            model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type
            )
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise TranscriptionError(f"Model loading failed: {e}")
    
    def get_model(self) -> WhisperModel:
        """Получить модель (загрузить если нужно)"""
        if self._model is None:
            self._model = self._load_model(
                self.config["asr_model_size"],
                self.config["asr_device"],
                self.config["asr_compute_type"]
            )
        return self._model
    
    def transcribe(self, audio_path: str) -> str:
        """Транскрибировать аудиофайл"""
        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Transcribing: {audio_path}")
        start_time = time.time()
        
        try:
            model = self.get_model()
            segments, info = model.transcribe(
                audio_path, 
                language="ru", 
                task="transcribe"
            )
            
            # Собираем текст
            text = " ".join([segment.text.strip() for segment in segments]).strip()
            
            transcribe_time = time.time() - start_time
            logger.info(f"Transcription completed in {transcribe_time:.2f}s")
            
            # Сохраняем транскрипт
            self._save_transcript(audio_path, text)
            
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Transcription error: {e}")
    
    def _save_transcript(self, audio_path: str, text: str) -> str:
        """Сохранить транскрипт в файл"""
        try:
            # Определяем тип записи по имени файла
            base_name = Path(audio_path).stem
            if base_name.startswith("meeting_"):
                out_dir = self.meetings_dir
            elif base_name.startswith("question_"):
                out_dir = self.questions_dir
            else:
                out_dir = self.transcripts_dir
            
            # Генерируем имя файла
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = out_dir / f"{base_name}_{ts}.txt"
            
            # Сохраняем
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            logger.info(f"Transcript saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")
            raise TranscriptionError(f"Failed to save transcript: {e}")
    
    def get_transcription_stats(self, audio_path: str) -> Dict[str, Any]:
        """Получить статистику транскрипции"""
        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        try:
            model = self.get_model()
            segments, info = model.transcribe(
                audio_path, 
                language="ru", 
                task="transcribe"
            )
            
            # Собираем статистику
            total_duration = sum(segment.end - segment.start for segment in segments)
            num_segments = len(list(segments))
            
            return {
                "total_duration": total_duration,
                "num_segments": num_segments,
                "language": info.language,
                "language_probability": info.language_probability
            }
            
        except Exception as e:
            logger.error(f"Failed to get transcription stats: {e}")
            raise TranscriptionError(f"Stats error: {e}")


# Функции для обратной совместимости
def load_asr_model(device: str = "cuda") -> WhisperModel:
    """Загрузка ASR модели (обратная совместимость)"""
    config = get_config()
    transcriber = OptimizedWhisperTranscriber(config)
    return transcriber.get_model()


def transcribe_with_faster_whisper(audio_path: str, asr_model: Optional[WhisperModel] = None) -> str:
    """Транскрипция с Faster-Whisper (обратная совместимость)"""
    config = get_config()
    transcriber = OptimizedWhisperTranscriber(config)
    return transcriber.transcribe(audio_path)

