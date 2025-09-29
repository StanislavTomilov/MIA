from __future__ import annotations
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

# ASR (faster-whisper)
from transcriber.whisper import transcribe_with_faster_whisper
# LLM-логика: саммари и задачи
from llms.tasks import make_summary, extract_tasks_struct

# RAG
from rag.embedder import Embedder
#from rag.search import FaissSearch  # если у тебя другой класс — см. комментарии ниже


# Состояние графа
class S(TypedDict, total=False):
    # Вход
    audio_path: str              # путь к аудио для полного пайплайна
    query: str                   # текст запроса для RAG по базе
    k: int                       # сколько результатов на RAG

    # Выходы узлов
    transcript_text: str
    transcript_segments: list
    asr_info: dict

    summary: str
    tasks: List[Dict[str, Any]]

    index_written: bool
    hits: List[Dict[str, Any]]


# --- Узлы графа ---

def asr_node(state: S) -> S:
    """
    Транскрибация аудио через faster-whisper.
    """
    out = transcribe_with_faster_whisper(
        state["audio_path"],
        device="cuda",        # при необходимости поменяй на "cpu"
        model_name="base",    # "large-v3" даст выше качество
        language="ru",
    )
    state["transcript_text"] = out["text"]
    state["transcript_segments"] = out["segments"]
    state["asr_info"] = out["info"]
    return state


def summary_node(state: S) -> S:
    """
    Делает саммари по полному тексту.
    """
    txt = state.get("transcript_text", "")
    state["summary"] = make_summary(txt) if txt else ""
    return state


def tasks_node(state: S) -> S:
    """
    Извлекает задачи (структурно: title, owner, due, priority, references...).
    """
    txt = state.get("transcript_text", "")
    sm = state.get("summary", "")
    state["tasks"] = extract_tasks_struct(txt, sm) if txt else []
    return state


def index_node(state: S) -> S:
#     """
#     Индексация summary в FAISS (или другом стораже, если у тебя свой класс).
#     """
    pass
#     summary = state.get("summary", "")
#     if not summary:
#         state["index_written"] = False
#         return state
#
#     # Встраивание
#     emb = Embedder()
#     vec = emb.encode_texts([summary])  # shape (1, dim)
#
#     # Хранилище (замени FaissSearch на твой класс, если имя другое)
#     idx = FaissSearch(dim=vec.shape[1])
#     try:
#         idx.load()  # пытаемся загрузить существующий индекс
#     except Exception:
#         pass
#
#     # id документа — из имени файла, чтобы потом можно было отследить
#     doc_id = "summary::" + state["audio_path"].split("/")[-1]
#     idx.add([doc_id], vec, metas=[{"type": "summary"}])
#     idx.save()
#
#     state["index_written"] = True
#     return state


def rag_query_node(state: S) -> S:
#     """
#     Поиск по базе встреч.
#     """
    pass
#     q = state.get("query", "")
#     k = state.get("k", 5)
#     emb = Embedder()
#     qv = emb.encode_texts([q])
#
#     idx = FaissSearch(dim=emb.dim())
#     idx.load()
#     state["hits"] = idx.search(qv, k=k)[0]  # ожидается список {id, score, meta?, text?}
#     return state
#

# --- Сборка графа ---

def build_pipeline_graph():
    """
    Полный маршрут: ASR -> Summary -> Tasks -> Index
    """
    g = StateGraph(S)
    g.add_node("asr", asr_node)
    g.add_node("summary", summary_node)
    g.add_node("tasks", tasks_node)
    g.add_node("index", index_node)

    g.set_entry_point("asr")
    g.add_edge("asr", "summary")
    g.add_edge("summary", "tasks")
    g.add_edge("tasks", "index")
    g.add_edge("index", END)
    return g.compile()


def build_rag_graph():
    """
    Только RAG-поиск: rag_query -> END
    """
    g = StateGraph(S)
    g.add_node("rag_query", rag_query_node)
    g.set_entry_point("rag_query")
    g.add_edge("rag_query", END)
    return g.compile()
