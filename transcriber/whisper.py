import whisperx
import torch

def transcribe_with_whisperx(audio_path, lang="ru", model_size="large-v2"):
    """
    Транскрибирует указанный аудиофайл через WhisperX.
    Возвращает словарь с текстом, словами и таймкодами.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔍 Загрузка модели WhisperX ({model_size}) на устройстве {device}...")
    model = whisperx.load_model(model_size, device)
    print("🚀 Транскрибация аудиофайла...")
    result = model.transcribe(audio_path, language=lang)
    print("✅ Транскрибация завершена.")
    return result
