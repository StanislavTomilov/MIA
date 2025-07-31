
import sys
import os
from transcriber.recorder import (
    record_audio_windows,
    record_audio_linux,
    record_audio_mac
)
from transcriber.whisper import (
    transcribe_with_whisperx,
    transcribe_with_whisperx_diarization
)
from transcriber.utils import save_transcript

from summarizer.summary import analyze_transcript_qwen3

def get_record_audio_func():
    if sys.platform.startswith("win"):
        return record_audio_windows
    elif sys.platform.startswith("linux"):
        return record_audio_linux
    elif sys.platform.startswith("darwin"):
        return record_audio_mac
    else:
        raise NotImplementedError(f"Платформа '{sys.platform}' не поддерживается")

if __name__ == "__main__":
    record_audio = get_record_audio_func()
    audio_path = record_audio(duration_sec=180)  # возвращает путь к файлу

    #audio_path = "/home/stanislav/PycharmProjects/MIA/audio/meeting_2025-07-30_07-12-30_linux.wav"

    result_aligned = transcribe_with_whisperx_diarization(audio_path, device="cuda", hf_token="REMOVED_HF_TOKEN")
    save_transcript(result_aligned, audio_path)

    # Извлекаем чистый текст
    transcript_text = " ".join([seg["text"].strip() for seg in result_aligned["segments"]])

    # Анализ встречи через Qwen3
    summary_json_str = analyze_transcript_qwen3(transcript_text)

    # Сохраняем summary
    os.makedirs("summaries", exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    with open(f"summaries/{base}_summary.json", "w", encoding="utf-8") as f:
        f.write(summary_json_str)
    print(f"✅ Саммари и задачи сохранены: summaries/{base}_summary.json")
