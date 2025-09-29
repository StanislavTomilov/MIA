import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-base"  # отличный ru/eng эмбеддер

class Embedder:
    def __init__(self, model_name: str = MODEL_NAME, device: str = None):
        # device=None => авто; можно "cuda" или "cpu"
        print(f"[RAG] Загружаю эмбеддер: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Возвращает np.ndarray float32 (N, d)
        """
        vecs = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=False   # нормализацию сделаем отдельно
        )
        return vecs.astype("float32")
