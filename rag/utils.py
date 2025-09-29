import os
import json
import numpy as np

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_json(path: str, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def l2_normalize(mat: np.ndarray) -> np.ndarray:
    """
    Нормализация строк матрицы до единичной длины (для cosine/IP).
    mat: (N, d) float32
    """
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return (mat / norms).astype("float32")
