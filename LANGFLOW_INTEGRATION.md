# 🚀 Интеграция MIA + Langflow

## 📋 Обзор

Этот документ описывает, как интегрировать Langflow с проектом MIA для создания визуальных пайплайнов обработки аудио и генерации ответов.

## ✅ Текущий статус

- ✅ Langflow 1.5.1 установлен и работает
- ✅ Все зависимости MIA совместимы
- ✅ Базовая интеграция протестирована
- ✅ Конфигурация централизована

## 🛠 Установка и настройка

### 1. Активация виртуального окружения
```bash
source .venv/bin/activate
```

### 2. Проверка установки
```bash
python3 test_langflow.py
```

### 3. Тест интеграции
```bash
python3 langflow_integration.py
```

## 🔧 Конфигурация

### Основные настройки (utils/config.py)
```python
# ASR настройки
ASR_DEVICE = "cpu"  # или "cuda"
ASR_MODEL_SIZE = "base"

# LLM настройки
LLM_HOST = "http://localhost:11434"
LLM_MODEL = "qwen3"

# Аудио настройки
SAMPLE_RATE = 48000
CHANNELS = 1
```

### Переключение режимов
```python
from utils.config import get_config

# Режим разработки (быстрый запуск)
config = get_config("development")

# Продакшн режим (максимальное качество)
config = get_config("production")
```

## 🎯 Возможности интеграции

### 1. Визуальные пайплайны
- Создание потоков обработки аудио
- Визуализация транскрипции
- Управление генерацией ответов

### 2. Компоненты MIA
- **AudioRecorder**: Запись аудио
- **WhisperTranscriber**: Транскрипция
- **LLMProcessor**: Обработка LLM
- **SummaryGenerator**: Генерация саммари

### 3. Пайплайны
- **Meeting Pipeline**: Полная обработка встречи
- **Question Pipeline**: Обработка вопросов
- **RAG Pipeline**: Поиск и генерация ответов

## 📊 Примеры использования

### Базовый пайплайн транскрипции
```python
from langflow import load_flow_from_json
from utils.config import get_config

# Загружаем конфигурацию
config = get_config()

# Создаем простой пайплайн
flow_config = {
    "nodes": [
        {
            "id": "audio_input",
            "type": "AudioInput",
            "data": {"sample_rate": config["sample_rate"]}
        },
        {
            "id": "transcriber",
            "type": "WhisperTranscriber",
            "data": {"device": config["asr_device"]}
        }
    ],
    "edges": [
        {"source": "audio_input", "target": "transcriber"}
    ]
}

# Загружаем пайплайн
flow = load_flow_from_json(flow_config)
```

### Пайплайн с LLM
```python
# Добавляем LLM обработку
flow_config["nodes"].append({
    "id": "llm_processor",
    "type": "LLMProcessor",
    "data": {
        "host": config["llm_host"],
        "model": config["llm_model"]
    }
})

flow_config["edges"].append({
    "source": "transcriber",
    "target": "llm_processor"
})
```

## 🔍 Мониторинг и отладка

### Логирование
- Логи сохраняются в `mia.log`
- Уровни: INFO, WARNING, ERROR
- Структурированный формат

### Тестирование
```bash
# Запуск всех тестов
python3 test_langflow.py

# Тест интеграции
python3 langflow_integration.py

# Тест основного приложения
python3 main.py
```

## 🚀 Запуск Langflow UI

### 1. Запуск веб-интерфейса
```bash
source .venv/bin/activate
langflow run --host 0.0.0.0 --port 7860
```

### 2. Открытие в браузере
```
http://localhost:7860
```

### 3. Создание пайплайна
1. Откройте Langflow UI
2. Создайте новый проект
3. Добавьте компоненты MIA
4. Настройте связи между компонентами
5. Сохраните и запустите пайплайн

## 📁 Структура файлов

```
MIA/
├── utils/
│   ├── config.py              # Конфигурация
│   ├── app_state.py           # Управление состоянием
│   ├── audio_manager.py       # Аудио менеджер
│   └── model_cache.py         # Кэш моделей
├── transcriber/
│   ├── whisper.py             # Транскрипция
│   └── whisper_optimized.py   # Оптимизированная версия
├── llms/
│   └── llm.py                 # LLM клиент
├── test_langflow.py           # Тесты
├── langflow_integration.py    # Пример интеграции
├── requirements_compatible.txt # Совместимые зависимости
└── LANGFLOW_INTEGRATION.md    # Эта документация
```

## 🐛 Решение проблем

### Проблема: Конфликт версий
```bash
# Проверьте установленные версии
pip list | grep torch
pip list | grep transformers

# Если есть конфликты, используйте совместимые версии
pip install -r requirements_compatible.txt
```

### Проблема: CUDA недоступен
```python
# В utils/config.py измените
ASR_DEVICE = "cpu"  # вместо "cuda"
```

### Проблема: Ollama недоступен
```bash
# Проверьте статус Ollama
ollama list

# Запустите Ollama если нужно
ollama serve
```

## 📈 Дальнейшее развитие

### 1. Кастомные компоненты
- Создание специализированных компонентов для MIA
- Интеграция с внешними API
- Поддержка различных форматов аудио

### 2. Расширенные пайплайны
- Обработка в реальном времени
- Параллельная обработка
- Очереди задач

### 3. Мониторинг
- Prometheus метрики
- Grafana дашборды
- Алерты и уведомления

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `mia.log`
2. Запустите тесты: `python3 test_langflow.py`
3. Проверьте конфигурацию в `utils/config.py`
4. Убедитесь, что все зависимости установлены

## 🎉 Заключение

Интеграция MIA + Langflow готова к использованию! Теперь вы можете:
- Создавать визуальные пайплайны обработки аудио
- Легко настраивать и модифицировать процессы
- Использовать все возможности MIA через удобный интерфейс
- Масштабировать и оптимизировать рабочие процессы

