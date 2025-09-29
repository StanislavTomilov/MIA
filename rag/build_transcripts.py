S# rag/build_transcripts.py
import numpy as np
import faiss
from rag.loader_transcripts import load_transcript_docs  # из rag/loader_transcripts.py
from rag.chunker import chunk_docs
from rag.embedder import Embedder
from rag.utils import l2_normalize, ensure_dir
import os, json

STORE_DIR = "rag_store_transcripts"

def main():
    docs = load_transcript_docs()                 # [{id, text, meta:{path,type}}]
    if not docs:
        print("[RAG] В transcripts/ нет данных.")
        return

    chunks = chunk_docs(docs, max_chars=1500, overlap=200)
    texts  = [c["text"] for c in chunks]
    metas  = [{"doc_id": c["doc_id"], "chunk_id": c["chunk_id"], **c["meta"]} for c in chunks]

    emb = Embedder()
    vecs = emb.encode(texts)
    vecs = l2_normalize(vecs)

    d = vecs.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(vecs)

    ensure_dir(STORE_DIR)
    faiss.write_index(index, os.path.join(STORE_DIR, "faiss.index"))
    with open(os.path.join(STORE_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)

    print(f"[RAG] Сохранено: {STORE_DIR}/faiss.index (+ meta.json), векторов: {len(metas)}")

if __name__ == "__main__":
    main()
