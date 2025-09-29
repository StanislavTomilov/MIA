# main.py

import os
import time
import threading
from pynput import keyboard as kb

from transcriber.recorder import Recorder
from transcriber.whisper import load_asr_model, transcribe_with_faster_whisper
from llms.llm import load_llm_client
from prompts.templates import get_corporate_summary_prompt, get_interview_prompt

from rag.embedder import Embedder
from rag.search import search
from prompts.templates import get_rag_answer_prompt
import faiss, json, os

# =========================
# Конфигурация и инициализация
# =========================
from utils.config import get_config

# Получаем конфигурацию
config = get_config()  # Можно изменить на "production" для продакшена

# Предзагрузка моделей (уменьшаем latency)
asr_model = load_asr_model(device=config["asr_device"])
llm_client = load_llm_client(host=config["llm_host"], model=config["llm_model"])
recorder = Recorder.create_auto(
    monitor_name=config["virtual_cable_name"],
    samplerate=config["sample_rate"],
    channels=config["channels"]
)

# Состояния (временно оставляем как есть, оптимизируем в следующем шаге)
is_meeting_active = False
is_question_active = False
pressed_keys = set()

# =========================
# Обработчики хоткеев
# =========================
def handle_meeting_recording():
    """
    Ctrl+R:
    - если не пишем → старт записи встречи (audio/meetings/*.wav)
    - если пишем → стоп, транскрипция (transcripts/meetings/*.txt), саммари → summaries/*.json
    """
    global is_meeting_active

    if not is_meeting_active:
        # Старт длительной записи встречи
        recorder.start_main_recording()
        print("▶️ Основная запись встречи начата (Ctrl+R чтобы остановить)")
        is_meeting_active = True
        return

    # Завершение записи встречи
    audio_path = recorder.stop_main_recording()
    print("⏹ Основная запись завершена. Обработка...")

    # Транскрибуем (функция сама положит текст в transcripts/meetings/*.txt)
    transcript_text = transcribe_with_faster_whisper(audio_path, asr_model=asr_model)

    # Формируем промпт саммари и получаем ответ от LLM (непотоково — это краткий JSON)
    prompt = get_corporate_summary_prompt(transcript_text)
    summary_json_str = llm_client.generate_answer(prompt)

    # Сохраняем саммари в summaries/
    os.makedirs("summaries", exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]  # meeting_...
    out_path = f"summaries/{base}_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary_json_str)
    print(f"✅ Саммари встречи сохранено: {out_path}")

    is_meeting_active = False


def handle_question_recording():
    """
    Ctrl+Q:
    - если не пишем вопрос → старт (audio/questions/*.wav)
    - если пишем → стоп, транскрипция (transcripts/questions/*.txt), потоковый ответ от LLM
    """
    global is_question_active

    if not is_question_active:
        # Защита: вопрос пишем только во время встречи (по твоей логике)
        if not is_meeting_active:
            print("Ошибка: Основная запись не идёт. Нельзя стартовать вопрос.")
            return

        recorder.start_question_recording()
        print("🔴 Запись вопроса начата (Ctrl+Q чтобы остановить)")
        is_question_active = True
        return

    # Завершение записи вопроса
    audio_path = recorder.stop_question_recording()
    print("🔵 Запись вопроса завершена. Обработка...")

    # Транскрибуем (функция сама положит текст в transcripts/questions/*.txt)
    question_text = transcribe_with_faster_whisper(audio_path, asr_model=asr_model)
    print(f"Вопрос: {question_text}")

    # Формируем промпт для интервью-ответа
    prompt = get_interview_prompt(question_text)

    # Таймер + потоковая генерация ответа
    start_time = time.perf_counter()
    for chunk in llm_client.generate_answer_stream(prompt):
        print(chunk, end='', flush=True)
    print()  # перенос строки после потока
    elapsed = time.perf_counter() - start_time
    print(f"⏱️ Ответ сгенерирован за {elapsed:.2f} сек.")

    is_question_active = False


# =========================
# Листенер хоткеев (pynput)
# =========================
def on_press(key):
    pressed_keys.add(key)

    # Ctrl+R — старт/стоп встречи
    if (kb.Key.ctrl_l in pressed_keys or kb.Key.ctrl_r in pressed_keys) and hasattr(key, 'char') and key.char in ('r', 'R'):
        threading.Thread(target=handle_meeting_recording, daemon=True).start()

    # Ctrl+Q — старт/стоп вопроса
    if (kb.Key.ctrl_l in pressed_keys or kb.Key.ctrl_r in pressed_keys) and hasattr(key, 'char') and key.char in ('q', 'Q'):
        threading.Thread(target=handle_question_recording, daemon=True).start()

    # ESC — выход
    if key == kb.Key.esc:
        print("Завершение работы.")
        return False  # остановить listener


def on_release(key):
    if key in pressed_keys:
        pressed_keys.remove(key)


def listen_hotkeys():
    print("====================================")
    print("Ctrl+R — старт/стоп записи всей встречи")
    print("Ctrl+Q — старт/стоп записи вопроса")
    print("ESC    — выход")
    print("====================================")
    with kb.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# === RAG по САММАРИ ===
def run_rag_chat_summaries():
    # Загрузка индекса и мета
    idx_path  = os.path.join("rag_store", "faiss.index")
    meta_path = os.path.join("rag_store", "meta.json")
    if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
        print("[RAG] Индекс по саммари не найден. Сначала: python -m rag.build")
        return
    index = faiss.read_index(idx_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metas = json.load(f)

    embedder = Embedder()

    print("\n[RAG] Чат по САММАРИ. Введите вопрос (или 'exit'):")
    while True:
        q = input("?> ").strip()
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            print("[RAG] Выход.")
            break

        q_vec = embedder.encode([q])                 # (1, d)
        hits  = search(index, metas, q_vec, top_k=5, threshold=0.32)

        # Для MVP подмешаем ссылки/идентификаторы найденных фрагментов
        lines = []
        for h in hits:
            p = h["meta"].get("path")
            doc_id = h["meta"].get("doc_id")
            chunk_id = h["meta"].get("chunk_id")
            lines.append(f"[summary:{doc_id}#chunk{chunk_id}] score={h['score']:.2f} | {p}")
        retrieved = "Найдены фрагменты саммари:\n" + ("\n".join(lines) if lines else "ничего не найдено")

        prompt = get_rag_answer_prompt(q, retrieved)

        print("\n--- Ответ (stream) ---")
        for chunk in llm_client.generate_answer_stream(prompt):
            print(chunk, end="", flush=True)
        print("\n----------------------\n")


# # === RAG по ТРАНСКРИБАЦИЯМ ===
# def run_rag_chat_transcripts():
#     idx_path  = os.path.join("rag_store_transcripts", "faiss.index")
#     meta_path = os.path.join("rag_store_transcripts", "meta.json")
#     if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
#         print("[RAG] Индекс по транскрибациям не найден. Сначала: python -m rag.build_transcripts")
#         return
#     index = faiss.read_index(idx_path)
#     with open(meta_path, "r", encoding="utf-8") as f:
#         metas = json.load(f)
#
#     embedder = Embedder()
#
#     print("\n[RAG-TX] Чат по ТРАНСКРИБАЦИЯМ. Введите вопрос (или 'exit'):")
#     while True:
#         q = input("?> ").strip()
#         if not q:
#             continue
#         if q.lower() in ("exit", "quit"):
#             print("[RAG-TX] Выход.")
#             break
#
#         q_vec = embedder.encode([q])
#         hits  = search(index, metas, q_vec, top_k=5, threshold=0.32)
#
#         lines = []
#         for h in hits:
#             p = h["meta"].get("path")
#             doc_id = h["meta"].get("doc_id")
#             chunk_id = h["meta"].get("chunk_id")
#             typ = h["meta"].get("type")
#             lines.append(f"[{typ}:{doc_id}#chunk{chunk_id}] score={h['score']:.2f} | {p}")
#         retrieved = "Найдены фрагменты транскрибаций:\n" + ("\n".join(lines) if lines else "ничего не найдено")
#
#         prompt = get_rag_answer_prompt(q, retrieved)
#
#         print("\n--- Ответ (stream) ---")
#         for chunk in llm_client.generate_answer_stream(prompt):
#             print(chunk, end="", flush=True)
#         print("\n----------------------\n")

if __name__ == "__main__":
    listen_hotkeys()

    run_rag_chat_summaries()

    run_rag_chat_transcripts()
