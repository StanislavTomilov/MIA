import numpy as np
from typing import List, Dict, Tuple
from .utils import l2_normalize

SIM_THRESHOLD = 0.32  # можно подстроить

def search(
    index,
    metas: List[Dict],
    query_vec: np.ndarray,
    top_k: int = 5,
    threshold: float = SIM_THRESHOLD
) -> List[Dict]:
    """
    query_vec: (1, d) float32 (не нормализован) -> нормализуем перед поиском
    """
    q = l2_normalize(query_vec)  # (1, d)
    D, I = index.search(q, top_k)  # D (1, k), I (1, k)

    results = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx == -1:
            continue
        if score < threshold:
            continue
        meta = metas[idx]
        results.append({
            "score": float(score),
            "meta": meta
        })
    return results
