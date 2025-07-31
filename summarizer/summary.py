from ollama import Client

client = Client(host='http://localhost:11434')

PROMPT = """
Ты корпоративный ассистент. Всегда отвечай только на русском языке.
Вот расшифровка встречи:

{transcript_text}

Сделай, пожалуйста, структурированный анализ:
- summary встречи (2-4 предложения)
- выдели все договорённости и принятые решения
- выпиши задачи в формате: [описание, ответственный, срок (если есть)]

Если в тексте нет явных задач или договорённостей, честно напиши, что их нет (например, "нет данных"). Не придумывай информацию, которой нет в тексте.
Ответ возвращай только в формате JSON и только на русском языке. Никаких объяснений, think-блоков, markdown и внутренних размышлений не писать.

Пример структуры:
{{
  "summary": "...",
  "agreements": ["..."],
  "tasks": [
    {{"task": "...", "responsible": "...", "deadline": "..."}},
    ...
  ]
}}
"""


def analyze_transcript_qwen3(transcript_text):
    print("⏳ [Qwen3] Начинаю анализ транскрипта...")
    print(f"🔸 Длина транскрипта: {len(transcript_text)} символов")
    print(f"🔸 Промпт для LLM (начало): {PROMPT[:200]}...")

    prompt_to_send = PROMPT.format(transcript_text=transcript_text)
    print(f"🔹 Фрагмент prompt для отправки (первые 500 символов):\n{prompt_to_send[:500]}...")

    try:
        response = client.generate(
            model='qwen3',
            prompt=prompt_to_send,
            stream=False
        )
    except Exception as e:
        print(f"❌ [Qwen3] Ошибка при вызове LLM: {e}")
        raise

    print("✅ [Qwen3] Модель вернула ответ. Длина ответа:", len(response['response']))
    print("🔹 Превью ответа (первые 500 символов):\n", response['response'][:500], "...")

    return response['response']
