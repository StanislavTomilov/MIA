from typing import List, Dict

def chunk_text(text: str, max_chars=1200, overlap=150) -> List[str]:
    """
    Простое посимвольное чанкинг c overlap.
    """
    chunks = []
    i, n = 0, len(text)
    while i < n:
        j = min(i + max_chars, n)
        chunks.append(text[i:j])
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks

def chunk_docs(docs: List[Dict], max_chars=1200, overlap=150) -> List[Dict]:
    """
    На выходе: список чанков:
    { "doc_id": str, "chunk_id": int, "text": str, "meta": {...} }
    """
    result = []
    for d in docs:
        parts = chunk_text(d["text"], max_chars=max_chars, overlap=overlap)
        for idx, t in enumerate(parts):
            result.append({
                "doc_id": d["id"],
                "chunk_id": idx,
                "text": t,
                "meta": d.get("meta", {})
            })
    print(f"[RAG] Чанков всего: {len(result)}")
    return result
