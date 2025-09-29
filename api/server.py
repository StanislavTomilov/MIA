from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import traceback
import uvicorn
import os

# Транскрибация
from transcriber.whisper import transcribe_with_faster_whisper
from llms.llm import load_llm_client
from rag.search import search  # сделай/проверь функцию: def rag_answer(question: str, top_k:int=5) -> dict

app = FastAPI(title="MIA API", version="0.1.0")

# -------- Модели запросов/ответов --------
class SummarizeIn(BaseModel):
    transcript: str
    meeting_id: Optional[str] = None
    meta: Optional[dict] = None

class TaskItem(BaseModel):
    title: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None

class SummaryOut(BaseModel):
    title: Optional[str] = None
    decisions: List[str] = []
    tasks: List[TaskItem] = []
    risks: List[str] = []
    next_steps: List[str] = []

class RagIn(BaseModel):
    question: str
    top_k: Optional[int] = 5

# -------- Health --------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------- 1) /transcribe --------
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Принимает аудиофайл (multipart/form-data), возвращает {"text": "..."}.
    """
    try:
        tmp_path = f"/tmp/{file.filename}"
        with open(tmp_path, "wb") as f:
            f.write(await file.read())
        text = transcribe_with_faster_whisper(tmp_path)
        os.remove(tmp_path)
        return {"text": text}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"transcribe_error: {e}")

# -------- 2) /summarize --------
@app.post("/summarize", response_model=SummaryOut)
def summarize(payload: SummarizeIn):
    """
    Принимает transcript и просит LLM вернуть структурированное JSON-summary.
    """
    try:
        client = load_llm_client(host="http://localhost:11434", model="qwen3")
        prompt = f"""
Ты — помощник протоколирования встреч. Верни ТОЛЬКО JSON без пояснений,
со следующими полями: 
  title: string,
  decisions: string[],
  tasks: {{ title: string, assignee?: string, due_date?: string }}[],
  risks: string[],
  next_steps: string[].

Текст стенограммы:
{payload.transcript}
"""
        raw = client.generate_answer(prompt).strip()

        # Мягкая защита: если LLM вернул не-JSON, обернём в “пустую” структуру
        import json
        try:
            data = json.loads(raw)
        except Exception:
            data = {
                "title": None,
                "decisions": [],
                "tasks": [],
                "risks": [],
                "next_steps": []
            }
        # Нормализация tasks
        tasks = []
        for t in data.get("tasks", []):
            if isinstance(t, dict):
                tasks.append({
                    "title": t.get("title") or "",
                    "assignee": t.get("assignee"),
                    "due_date": t.get("due_date")
                })
            else:
                tasks.append({"title": str(t)})

        return SummaryOut(
            title=data.get("title"),
            decisions=data.get("decisions", []),
            tasks=[TaskItem(**x) for x in tasks],
            risks=data.get("risks", []),
            next_steps=data.get("next_steps", [])
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"summarize_error: {e}")

# -------- 3) /rag/search --------
@app.post("/rag/search")
def rag_search(payload: RagIn):
    """
    Принимает question, возвращает {"answer": "...", "chunks": [...]}
    где chunks — найденные фрагменты/метаданные.
    """
    try:
        result = search(payload.question, top_k=payload.top_k or 5)
        return JSONResponse(result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"rag_error: {e}")

# Локальный запуск (опционально)
if __name__ == "__main__":
    uvicorn.run("api.server:app", host="127.0.0.1", port=5001, reload=True)
