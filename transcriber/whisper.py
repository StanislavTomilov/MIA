import whisperx
from whisperx import load_align_model, align
from pyannote.audio import Pipeline
import torch


def transcribe_with_whisperx(audio_path: str, model_size: str = "large-v3", language: str = "ru", device: str = "cuda"):

    import torch
    print(f"[🧠] torch.cuda.is_available() = {torch.cuda.is_available()}")
    print(f"[🧠] torch version: {torch.__version__}")
    print(f"[🧠] CUDA device: {torch.cuda.get_device_name(0)}")

    print(f"[🔍] Загружаем модель: {model_size} на {device}...")
    model = whisperx.load_model(model_size, device, language=language)

    print(f"[🎧] Распознаём аудио: {audio_path}...")
    result = model.transcribe(audio_path)

    print("[📌] Базовая транскрипция:")
    for segment in result["segments"]:
        print(f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}")

    # print("\n[🔁] Запускаем выравнивание по словам...")
    # model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
    # result_aligned = whisperx.align(result["segments"], model_a, metadata, audio_path, device)
    #
    # print("\n[✅] Выравненные сегменты:")
    # for seg in result_aligned["segments"]:
    #     words = " ".join([w["word"] for w in seg["words"]])
    #     print(f"[{seg['start']:.2f} - {seg['end']:.2f}] {words}")

    return result


def transcribe_with_whisperx_diarization(audio_path, hf_token, min_speakers=1, max_speakers=10, device="cuda"):
    # 1. Транскрипция
    model = whisperx.load_model("large-v3", device)
    result = model.transcribe(audio_path)

    # 2. Diarization через Pyannote
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
    diar = pipeline(audio_path, min_speakers=min_speakers, max_speakers=max_speakers)

    diarized = []
    for seg in result["segments"]:
        speaker = "unknown"
        for turn, _, label in diar.itertracks(yield_label=True):
            if seg["start"] < turn.end and seg["end"] > turn.start:
                speaker = label
                break
        seg["speaker"] = speaker
        diarized.append(seg)
    print(f"Результат diarization: {diarized}")

    aligned_model, metadata = whisperx.load_align_model(language_code="ru", device=device)
    aligned = align(diarized, aligned_model, metadata, audio_path, device=device)
    return aligned


from diarizen.pipelines.inference import DiariZenPipeline
from your_asr_module import transcribe_with_whisperx  # ваша ASR
from llm_client import LLMClient  # ваш клиент для call LLM
import json

# 1. Загружаем DiariZen pipeline
diar_pipeline = DiariZenPipeline.from_pretrained("BUT-FIT/diarizen-meeting-base")

# 2. Функция LLM-коррекции
PROMPT_TEMPLATE = """
Исправь метки говорящих, если есть ошибки:

{turns}

Ответ в формате:
speaker_id <корректный номер>, start, end
...
"""


def correct_diarization_with_llm(asr_segments, speaker_labels, llm_client):
    # Собираем turns
    lines = []
    for seg, sp in zip(asr_segments, speaker_labels):
        text = seg["text"].strip()
        lines.append(f"{sp}: {text}")
    prompt = PROMPT_TEMPLATE.format(turns="\n".join(lines))
    resp = llm_client.generate(prompt)
    # Преобразуем ответ
    corrected = {}
    for line in resp.splitlines():
        parts = line.split(',')
        sid, start, end = parts[0].strip(), float(parts[1]), float(parts[2])
        corrected[(start, end)] = sid
    return corrected


def diarize_and_correct(audio_path, hf_token, llm_client):
    # ASR + raw diarization
    asr = transcribe_with_whisperx(audio_path, device="cuda")
    diar = diar_pipeline(audio_path)

    segments, labels = [], []
    for seg, _, sp in diar.itertracks(yield_label=True):
        segments.append({"start": seg.start, "end": seg.end})
        labels.append(f"speaker_{sp}")

    # LLM-коррекция
    corrected = correct_diarization_with_llm(segments, labels, llm_client)

    # Мержим: заменяем speaker в asr["segments"]
    new_segments = []
    for seg in asr["segments"]:
        for (s, e), sid in corrected.items():
            if seg["start"] < e and seg["end"] > s:
                seg["speaker"] = sid
                break
        new_segments.append(seg)
    return {"segments": new_segments}
