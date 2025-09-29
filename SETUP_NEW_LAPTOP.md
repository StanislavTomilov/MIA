# 🚀 Установка MIA проекта на новый ноутбук

## 📋 Что включено в проект

✅ **Полностью рабочий проект MIA с интеграцией Langflow**
- Кастомные компоненты для записи аудио
- RAG система для работы с транскриптами и саммари
- Оптимизированный main.py
- Полная документация

## 🔧 Быстрая установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/StanislavTomilov/MIA.git
cd MIA
```

### 2. Создание виртуального окружения
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Установка Langflow (версия 1.4.3)
```bash
pip install langflow==1.4.3
```

### 5. Запуск Langflow с кастомными компонентами
```bash
source .venv/bin/activate
langflow run --host 0.0.0.0 --port 7860 --components-path "$(pwd)/custom_components"
```

## 🎯 Основные компоненты

### AudioRecorderComponent
- 🎤 Запись встреч и вопросов
- 🔴 Интерактивные кнопки управления
- ⚙️ Предустановленные оптимальные параметры
- 📊 Статус записи в реальном времени

### RAG система
- 📝 Обработка транскриптов
- 📄 Создание саммари
- 🔍 Поиск по содержимому
- 💾 Индексация данных

## 📁 Структура проекта

```
MIA/
├── custom_components/          # Кастомные компоненты Langflow
│   ├── audio_recorder.py      # 🎤 Основной аудио компонент
│   └── __init__.py
├── langflow_local_backup/     # Резервные копии
├── rag/                       # RAG система
├── transcriber/              # Транскрипция
├── utils/                    # Утилиты
├── main_optimized.py         # Оптимизированная версия
├── requirements.txt          # Зависимости
└── README.md
```

## 🚨 Важные замечания

1. **Аудиофайлы не включены** - они слишком большие для GitHub
2. **Используйте Langflow 1.4.3** - в новых версиях есть баги с кастомными компонентами
3. **Компоненты в папке `custom_components/`** - Langflow автоматически их найдет

## 🔗 Полезные ссылки

- [Документация Langflow](https://docs.langflow.org/)
- [GitHub репозиторий](https://github.com/StanislavTomilov/MIA)
- [Интеграция с Langflow](LANGFLOW_INTEGRATION.md)

## 🆘 Если что-то не работает

1. Проверьте версию Langflow: `langflow --version`
2. Убедитесь, что используете `--components-path`
3. Проверьте логи в терминале
4. Перезапустите Langflow

---
**Готово к работе! 🎉**
