import os
from transcriber.recorder import Recorder
from transcriber.whisper import transcribe_with_faster_whisper
from prompts.templates import get_interview_summary_prompt

def protocol_pipeline(
    device,
    asr_model=None,
    llm_client=None
):
    """
    device: 'cuda' или 'cpu'
    asr_model: инициализированная Faster-Whisper модель
    llm_client: инициализированный клиент LLM
    """

    # 1. Запуск основной записи встречи
    recorder = Recorder()
    recorder.start_main_recording()
    print("Запись основной встречи начата. Для завершения — нажмите Enter.")
    input()  # Ждём, пока пользователь завершит встречу
    audio_path = recorder.stop_main_recording()

    # 2. Транскрибация встречи
    transcript_text = transcribe_with_faster_whisper(audio_path, asr_model=asr_model)

    # 3. Генерация промпта для LLM через шаблон
    prompt = get_interview_summary_prompt().format(transcript_text=transcript_text)
    summary_json_str = llm_client.generate_answer(prompt)

    # 4. Сохраняем результат
    os.makedirs("summaries", exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    with open(f"summaries/{base}_summary.json", "w", encoding="utf-8") as f:
        f.write(summary_json_str)
    print(f"✅ Саммари и задачи сохранены: summaries/{base}_summary.json")



# import os
# from transcriber.recorder import get_record_audio_func
# from transcriber.whisper import transcribe_with_whisperx_diarization
# from transcriber.utils import save_transcript
# from llms.llm import analyze_transcript_qwen3
#
# def protocol_pipeline(
#     duration_sec,
#     device,
#     hf_token,
#     asr_model=None,
#     llm_client=None
# ):
#     record_audio = get_record_audio_func()
#     audio_path = record_audio(duration_sec=duration_sec)
#     # Здесь asr_model не используется, но оставляем для совместимости структуры
#     result_aligned = transcribe_with_whisperx_diarization(
#         audio_path,
#         device=device,
#         hf_token=hf_token,
#         asr_model=asr_model
#     )
#     save_transcript(result_aligned, audio_path)
#     transcript_text = " ".join([seg["text"].strip() for seg in result_aligned["segments"]])
#     summary_json_str = analyze_transcript_qwen3(
#         transcript_text,
#         llm_client=llm_client
#     )
#     os.makedirs("summaries", exist_ok=True)
#     base = os.path.splitext(os.path.basename(audio_path))[0]
#     with open(f"summaries/{base}_summary.json", "w", encoding="utf-8") as f:
#         f.write(summary_json_str)
#     print(f"✅ Саммари и задачи сохранены: summaries/{base}_summary.json")
