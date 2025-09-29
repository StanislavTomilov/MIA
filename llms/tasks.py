# llms/tasks.py
import json
from typing import List, Dict, Any, Optional

from llms.llm import load_llm_client, LocalLLMClient
from prompts.prompts import SUMMARY_PROMPT, TASKS_PROMPT

def make_summary(transcript_text: str, llm: Optional[LocalLLMClient] = None) -> str:
    """
    Делает компактное саммари по транскрипту.
    """
    if not transcript_text or not transcript_text.strip():
        return ""

    llm = llm or load_llm_client()
    prompt = SUMMARY_PROMPT.format(transcript=transcript_text)
    try:
        summary = llm.generate_answer(prompt)
        return (summary or "").strip()
    except Exception as e:
        print(f"[LLM Summary] Ошибка: {e}")
        return ""

def extract_tasks_struct(transcript_text: str, summary: str = "", llm: Optional[LocalLLMClient] = None) -> List[Dict[str, Any]]:
    """
    Извлекает задачи в структурированном JSON-формате.
    Возвращает список словарей (tasks).
    """
    if not transcript_text or not transcript_text.strip():
        return []

    llm = llm or load_llm_client()
    prompt = TASKS_PROMPT.format(transcript=transcript_text, summary=summary or "нет")
    try:
        raw = llm.generate_answer(prompt)
        # защитный парсинг
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end+1]
        data = json.loads(raw)
        tasks = data.get("tasks") or []
        # валидация минимальных полей
        norm = []
        for t in tasks:
            norm.append({
                "title": t.get("title") or "",
                "description": t.get("description") or "",
                "assignee": t.get("assignee"),
                "due_date": t.get("due_date"),
                "priority": t.get("priority") or "medium",
                "source": t.get("source") or "",
            })
        return norm
    except Exception as e:
        print(f"[LLM Tasks] Ошибка парсинга ответа LLM: {e}")
        return []
