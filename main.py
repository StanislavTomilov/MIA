import sys
from transcriber.recorder import (
    record_audio_windows,
    record_audio_linux,
    record_audio_mac
)

def get_record_audio_func():
    if sys.platform.startswith("win"):
        return record_audio_windows
    elif sys.platform.startswith("linux"):
        return record_audio_linux
    elif sys.platform.startswith("darwin"):  # macOS
        return record_audio_mac
    else:
        raise NotImplementedError(f"Платформа '{sys.platform}' не поддерживается")

if __name__ == "__main__":
    record_audio = get_record_audio_func()
    record_audio(duration_sec=10)
