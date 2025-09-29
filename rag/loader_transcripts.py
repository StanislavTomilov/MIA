# rag/loader_transcripts.py
import os
import glob
from typing import List, Dict

TRANSCRIPTS_ROOT = "transcripts"
MEETINGS_DIR     = os.path.join(TRANSCRIPTS_ROOT, "meetings")
QUESTIONS_DIR    = os.path.join(TRANSCRIPTS_ROOT, "questions")

def _load_txt_files(folder: str, kind: str) -> List[Dict]:
    paths = sorted(glob.glob(os.path.join(folder, "*.txt")))
    docs = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                txt = f.read().strip()
            if not txt:
                continue
            docs.append({
                "id": os.path.basename(p),
                "text": txt,
                "meta": {
                    "path": p,
                    "type": kind  # "meeting" | "question"
                }
            })
        except Exception as e:
            print(f"[RAG] Ошибка чтения транскрипции {p}: {e}")
    return docs

def load_transcript_docs() -> List[Dict]:
    """
    Возвращает список документов из транскрибаций:
    [{id, text, meta:{path, type}}]
    """
    docs = []
    docs += _load_txt_files(MEETINGS_DIR,  "meeting")
    docs += _load_txt_files(QUESTIONS_DIR, "question")
    print(f"[RAG] Загружено транскрибаций: {len(docs)} "
          f"(meetings={len([d for d in docs if d['meta']['type']=='meeting'])}, "
          f"questions={len([d for d in docs if d['meta']['type']=='question'])})")
    return docs
