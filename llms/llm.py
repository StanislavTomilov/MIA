import requests
import json

class LocalLLMClient:
    def __init__(self, host="http://localhost:11434", model="qwen3"):
        self.host = host
        self.model = model

    def generate_answer_stream(self, prompt):
        """
        Отправляет prompt в Ollama (stream=True) и возвращает генератор с частями ответа.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        # stream=True позволяет читать по частям (Response.iter_lines)
        with requests.post(url, json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        # Ollama возвращает токены в поле "response"
                        # Некоторые модели — в "message"
                        chunk = data.get("response") or data.get("message")
                        if chunk:
                            yield chunk
                    except Exception as e:
                        print(f"[Ollama Stream] Ошибка парсинга: {e}")

    # Обычный (не потоковый) метод для обратной совместимости

    def generate_answer(self, prompt):
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        resp = requests.post(url, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response") or data.get("message") or str(data)

def load_llm_client(host="http://localhost:11434", model="qwen3"):
    """
    Инициализация клиента локального LLM (вызывается один раз)
    """
    print(f"⏳ Запуск локального LLM-клиента ({model}, {host})...")
    return LocalLLMClient(host=host, model=model)


# from ollama import Client
#
# client = Client(host='http://localhost:11434')
#
# def analyze_transcript_qwen3(transcript_text):
#     print("⏳ [Qwen3] Начинаю анализ транскрипта...")
#     print(f"🔸 Длина транскрипта: {len(transcript_text)} символов")
#     print(f"🔸 Промпт для LLM (начало): {PROMPT[:200]}...")
#
#     prompt_to_send = PROMPT.format(transcript_text=transcript_text)
#     print(f"🔹 Фрагмент prompt для отправки (первые 500 символов):\n{prompt_to_send[:500]}...")
#
#     try:
#         response = client.generate(
#             model='qwen3',
#             prompt=prompt_to_send,
#             stream=False
#         )
#     except Exception as e:
#         print(f"❌ [Qwen3] Ошибка при вызове LLM: {e}")
#         raise
#
#     print("✅ [Qwen3] Модель вернула ответ. Длина ответа:", len(response['response']))
#     print("🔹 Превью ответа (первые 500 символов):\n", response['response'][:500], "...")
#
#     return response['response']

