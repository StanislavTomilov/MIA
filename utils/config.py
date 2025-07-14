# utils/config.py

import os

# Базовая директория (где лежит main.py)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Директории
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Параметры записи
SAMPLE_RATE = 16000  # 16kHz — идеально для Whisper
