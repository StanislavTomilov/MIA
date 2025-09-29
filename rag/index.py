import os
import faiss
import numpy as np
from typing import List, Dict, Tuple
from .utils import ensure_dir, save_json, load_json, l2_normalize

INDEX_DIR = "rag_store"
INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")
META_PATH  = os.path.join(INDEX_DIR, "meta.json")

def build_and_save_index(embeddings: np.ndarray, metas: List[Dict]):
    """
    embeddings: (N, d) float32 — нормализуем и строим IndexFlatIP
    metas: список мета-инфо для каждого вектора (len == N)
    """
    ensure_dir(INDEX_DIR)

    # Нормализуем для cosine через IP
    embs = l2_normalize(embeddings)
    d = embs.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(embs)
    faiss.write_index(index, INDEX_PATH)
    save_json(META_PATH, metas)
    print(f"[RAG] Индекс сохранён: {INDEX_PATH}, мета: {META_PATH}, векторов: {embs.shape[0]}")

def load_index() -> Tuple[faiss.Index, List[Dict]]:
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        raise RuntimeError("[RAG] Индекс не найден. Сначала соберите его (build).")
    index = faiss.read_index(INDEX_PATH)
    metas = load_json(META_PATH)
    print(f"[RAG] Индекс загружен: {INDEX_PATH}, мета: {len(metas)}")
    return index, metas
