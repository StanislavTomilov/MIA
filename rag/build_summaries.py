# rag/build.py
import numpy as np
import faiss
from rag.loader_summaries import load_summary_docs         # из rag/loader.py (саммари → docs)
from rag.chunker import chunk_docs               # из rag/chunker.py (нарезка)
from rag.embedder import Embedder                # из rag/embedder.py (эмбеддер)
from rag.utils import l2_normalize, ensure_dir
import os, json

STORE_DIR = "rag_store"                          # куда класть индекс и мета

def main():
    docs = load_summary_docs()                   # [{id, text, meta}]
    if not docs:
        print("[RAG] В summaries/ нет данных.")
        return

    chunks = chunk_docs(docs, max_chars=1200, overlap=150)
    texts  = [c["text"] for c in chunks]
    metas  = [{"doc_id": c["doc_id"], "chunk_id": c["chunk_id"], **c["meta"]} for c in chunks]

    emb = Embedder()
    vecs = emb.encode(texts)                     # (N, d) float32
    vecs = l2_normalize(vecs)                    # для cosine (IP)

    d = vecs.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(vecs)

    # save
    ensure_dir(STORE_DIR)
    faiss.write_index(index, os.path.join(STORE_DIR, "faiss.index"))
    with open(os.path.join(STORE_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    print(f"[RAG] Сохранено: {STORE_DIR}/faiss.index (+ meta.json), векторов: {len(metas)}")

if __name__ == "__main__":
    main()
