import os
import json

def save_transcript(result_aligned, audio_path, transcripts_dir="transcripts"):
    """
    Сохраняет выровненную транскрипцию (result_aligned) в transcripts/<имя>.json
    """
    os.makedirs(transcripts_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    transcript_file = os.path.join(transcripts_dir, base + ".json")

    with open(transcript_file, "w", encoding="utf-8") as f:
        json.dump(result_aligned, f, ensure_ascii=False, indent=2)
    print(f"✅ Транскрибация сохранена: {transcript_file}")
