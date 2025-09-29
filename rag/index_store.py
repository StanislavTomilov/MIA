# rag/index_store.py
import os
import faiss
from typing import List, Dict, Tuple
from .utils import ensure_dir, save_json, load_json

class IndexStore:
    def __init__(self, base_dir: str):
        """
        base_dir: каталог с индексом и метаданными
        """
        self.base_dir = base_dir
        self.index_path = os.path.join(base_dir, "faiss.index")
        self.meta_path  = os.path.join(base_dir, "meta.json")

    def save(self, index: faiss.Index, metas: List[Dict]):
        ensure_dir(self.base_dir)
        faiss.write_index(index, self.index_path)
        save_json(self.meta_path, metas)
        print(f"[RAG] Индекс сохранён: {self.index_path}, мета: {self.meta_path}, векторов: {len(metas)}")

    def load(self) -> Tuple[faiss.Index, List[Dict]]:
        if not (os.path.exists(self.index_path) and os.path.exists(self.meta_path)):
            raise RuntimeError(f"[RAG] Индекс не найден в {self.base_dir}. Сначала соберите его.")
        index = faiss.read_index(self.index_path)
        metas = load_json(self.meta_path)
        print(f"[RAG] Индекс загружен: {self.index_path}, мета-объектов: {len(metas)}")
        return index, metas
