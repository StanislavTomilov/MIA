# utils/config.py

import os
from pathlib import Path
from typing import Dict, Any

# Базовая директория (где лежит main.py)
BASE_DIR = Path(__file__).parent.parent.absolute()

# Директории
AUDIO_DIR = BASE_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "output"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
SUMMARIES_DIR = BASE_DIR / "summaries"
RAG_STORE_DIR = BASE_DIR / "rag_store"

# Параметры записи
SAMPLE_RATE = 48000  # 48kHz для лучшего качества
CHANNELS = 1
AUDIO_FORMAT = "s16le"

# Параметры ASR
ASR_MODEL_SIZE = "base"  # "tiny", "base", "small", "medium", "large"
ASR_DEVICE = "cuda"  # "cuda" или "cpu"
ASR_COMPUTE_TYPE = "float16"  # "float16", "int8", "int8_float16"

# Параметры LLM
LLM_HOST = "http://localhost:11434"
LLM_MODEL = "qwen3"
LLM_TIMEOUT = 180

# Параметры RAG
RAG_MODEL_NAME = "intfloat/multilingual-e5-base"
RAG_TOP_K = 5
RAG_THRESHOLD = 0.32
RAG_BATCH_SIZE = 32

# Параметры аудио
VIRTUAL_CABLE_NAME = "VirtualCable.monitor"
AUDIO_LATENCY_MS = 50

# Создание директорий
for directory in [AUDIO_DIR, OUTPUT_DIR, TRANSCRIPTS_DIR, SUMMARIES_DIR, RAG_STORE_DIR]:
    directory.mkdir(exist_ok=True)

# Конфигурация для разных режимов
CONFIGS = {
    "development": {
        "asr_model_size": "tiny",
        "asr_device": "cpu",
        "llm_timeout": 60,
    },
    "production": {
        "asr_model_size": "large",
        "asr_device": "cuda",
        "llm_timeout": 300,
    }
}

def get_config(env: str = "development") -> Dict[str, Any]:
    """Получить конфигурацию для указанного окружения"""
    base_config = {
        "base_dir": str(BASE_DIR),
        "audio_dir": str(AUDIO_DIR),
        "transcripts_dir": str(TRANSCRIPTS_DIR),
        "summaries_dir": str(SUMMARIES_DIR),
        "rag_store_dir": str(RAG_STORE_DIR),
        "sample_rate": SAMPLE_RATE,
        "channels": CHANNELS,
        "asr_model_size": ASR_MODEL_SIZE,
        "asr_device": ASR_DEVICE,
        "asr_compute_type": ASR_COMPUTE_TYPE,
        "llm_host": LLM_HOST,
        "llm_model": LLM_MODEL,
        "llm_timeout": LLM_TIMEOUT,
        "rag_model_name": RAG_MODEL_NAME,
        "rag_top_k": RAG_TOP_K,
        "rag_threshold": RAG_THRESHOLD,
        "rag_batch_size": RAG_BATCH_SIZE,
        "virtual_cable_name": VIRTUAL_CABLE_NAME,
        "audio_latency_ms": AUDIO_LATENCY_MS,
    }
    
    if env in CONFIGS:
        base_config.update(CONFIGS[env])
    
    return base_config
