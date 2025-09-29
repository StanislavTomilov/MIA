import os
import glob
import json
from typing import List, Dict

# Мы делаем RAG по САММАРИ встреч
SUMMARIES_DIR = "summaries"   # тут лежат meeting_*_summary.json

def load_summary_docs() -> List[Dict]:
    """
    Читает все JSON из summaries/ и превращает их в список документов.
    Каждый документ: {"id": str, "text": str, "meta": {...}}
    """
    paths = sorted(glob.glob(os.path.join(SUMMARIES_DIR, "*.json")))
    docs = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ожидаем структуру:
            # {
            #   "summary": "...",
            #   "agreements": ["...", ...],
            #   "tasks": [{"task":"...", "responsible":"...", "deadline":"..."}, ...]
            # }
            summary_txt = data.get("summary", "")
            agreements = data.get("agreements", [])
            tasks = data.get("tasks", [])

            tasks_lines = []
            for t in tasks:
                task = t.get("task") or ""
                responsible = t.get("responsible") or ""
                deadline = t.get("deadline") or ""
                tasks_lines.append(f"- {task} | {responsible} | {deadline}")

            text = ""
            if summary_txt:
                text += f"Итоговое саммари:\n{summary_txt}\n\n"
            if agreements:
                text += "Договорённости:\n" + "\n".join(f"- {a}" for a in agreements) + "\n\n"
            if tasks_lines:
                text += "Задачи:\n" + "\n".join(tasks_lines) + "\n"

            if not text.strip():
                continue

            docs.append({
                "id": os.path.basename(p),
                "text": text.strip(),
                "meta": {"path": p}
            })
        except Exception as e:
            print(f"[RAG] Ошибка чтения {p}: {e}")
    print(f"[RAG] Загружено документов из summaries/: {len(docs)}")
    return docs
