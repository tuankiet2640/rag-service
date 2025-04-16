import os
import faiss
import numpy as np
from typing import List, Tuple

def get_index_path(kb_name: str):
    safe_kb = kb_name.replace("/", "_").replace("\\", "_")
    dir_path = os.path.join(os.getcwd(), "indexes", safe_kb)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, "faiss.index")

class FAISSManager:
    """
    Handles FAISS index creation, persistence, and similarity search.
    Stores embeddings in-memory or on disk.
    """
    def __init__(self, dim: int, index_path: str = None):
        self.dim = dim
        self.index_path = index_path or os.getenv("FAISS_INDEX_PATH", "faiss.index")
        self.index = faiss.IndexFlatL2(dim)
        self.id_to_chunk = {}  # Maps FAISS vector id to chunk metadata
        if os.path.exists(self.index_path):
            self.load_index()

    def add_embeddings(self, embeddings: List[np.ndarray], chunk_ids: List[str]):
        arr = np.vstack(embeddings).astype(np.float32)
        start_id = self.index.ntotal
        self.index.add(arr)
        for i, chunk_id in enumerate(chunk_ids):
            self.id_to_chunk[start_id + i] = chunk_id
        self.save_index()

    def search(self, query_emb: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
        D, I = self.index.search(query_emb.reshape(1, -1).astype(np.float32), top_k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            if idx == -1:
                continue
            chunk_id = self.id_to_chunk.get(idx)
            if chunk_id:
                results.append((chunk_id, float(dist)))
        return results

    def save_index(self):
        faiss.write_index(self.index, self.index_path)
        # Save id_to_chunk mapping
        np.save(self.index_path + ".chunks.npy", self.id_to_chunk)

    def load_index(self):
        self.index = faiss.read_index(self.index_path)
        if os.path.exists(self.index_path + ".chunks.npy"):
            self.id_to_chunk = np.load(self.index_path + ".chunks.npy", allow_pickle=True).item()

    def reset(self):
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_to_chunk = {}
        self.save_index()
