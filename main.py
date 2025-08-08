import os, time
from pynput import keyboard as kb
import threading
from transcriber.recorder import Recorder
from transcriber.whisper import load_asr_model, transcribe_with_faster_whisper
from llms.llm import load_llm_client
from prompts.templates import get_corporate_summary_prompt, get_interview_prompt

# Инициализация моделей
asr_model = load_asr_model()
llm_client = load_llm_client()
recorder = Recorder.create_auto()
is_meeting_active = False
is_question_active = False

# Сохраняем состояние зажатых клавиш
pressed_keys = set()

def handle_meeting_recording():
    global is_meeting_active
    if not is_meeting_active:
        recorder.start_main_recording()
        print("▶️ Основная запись встречи начата (Ctrl+R чтобы остановить)")
        is_meeting_active = True
    else:
        audio_path = recorder.stop_main_recording()
        print("⏹ Основная запись завершена. Обработка...")
        transcript_text = transcribe_with_faster_whisper(audio_path, asr_model=asr_model)
        prompt = get_corporate_summary_prompt(transcript_text)
        summary_json_str = llm_client.generate_answer(prompt)
        os.makedirs("summaries", exist_ok=True)
        base = os.path.splitext(os.path.basename(audio_path))[0]
        with open(f"summaries/{base}_summary.json", "w", encoding="utf-8") as f:
            f.write(summary_json_str)
        print(f"✅ Саммари встречи сохранено: summaries/{base}_summary.json")
        is_meeting_active = False

def handle_question_recording():
    global is_question_active
    if not is_question_active:
        if not is_meeting_active:
            print("Ошибка: Основная запись не идёт. Нельзя стартовать вопрос.")
            return
        recorder.start_question_recording()
        is_question_active = True
    else:
        audio_path = recorder.stop_question_recording()
        print("🔵 Запись вопроса завершена. Обработка...")
        question_text = transcribe_with_faster_whisper(audio_path, asr_model=asr_model)
        print(f"Вопрос: {question_text}")
        prompt = get_interview_prompt(question_text)

        start_time = time.perf_counter()  # Засекаем время до вызова LLM

        # answer = llm_client.generate_answer(prompt)
        for chunk in llm_client.generate_answer_stream(prompt):
            print(chunk, end='', flush=True)  # Выводим по мере генерации
        print()  # Для переноса строки после ответа

        end_time = time.perf_counter()  # Засекаем время после завершения
        elapsed = end_time - start_time  # Считаем разницу

        print(f"⏱️ Ответ сгенерирован за {elapsed:.2f} сек.")

        is_question_active = False

def on_press(key):
    pressed_keys.add(key)
    # Проверка нажатия Ctrl+R
    if (kb.Key.ctrl_l in pressed_keys or kb.Key.ctrl_r in pressed_keys) and hasattr(key, 'char') and key.char in ('r', 'R'):
        threading.Thread(target=handle_meeting_recording).start()
    # Проверка нажатия Ctrl+Q
    if (kb.Key.ctrl_l in pressed_keys or kb.Key.ctrl_r in pressed_keys) and hasattr(key, 'char') and key.char in ('q', 'Q'):
        threading.Thread(target=handle_question_recording).start()
    # Проверка нажатия ESC
    if key == kb.Key.esc:
        print("Завершение работы.")
        return False  # Остановить listener

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

if __name__ == "__main__":
    listen_hotkeys()
