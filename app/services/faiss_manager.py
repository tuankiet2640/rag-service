import numpy as np
import faiss
import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Centralized function to get the full index path
def get_index_path(kb_id: str):
    """Constructs the full path for the FAISS index file based on KB ID."""
    base_path = os.getenv("VECTOR_STORE_PATH", "./data/vector_stores")
    # Ensure the base directory exists
    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path, exist_ok=True)
            logger.info(f"Created vector store directory: {base_path}")
        except OSError as e:
            logger.error(f"Failed to create vector store directory {base_path}: {e}", exc_info=True)
            # Depending on requirements, might raise exception or return None
            raise e # Re-raise for now
    # Return the full path including the filename
    return os.path.join(base_path, f"{kb_id}.faiss")


class FAISSManager:
    """Handles FAISS index creation, persistence, and similarity search."""

    # Removed default value and os.getenv logic for index_path
    def __init__(self, dim: int, index_path: str):
        """Initializes the FAISS manager.

        Args:
            dim: The dimensionality of the vectors.
            index_path: The full path to the FAISS index file.
        """
        self.dim = dim
        self.index_path = index_path
        # Use a thread-safe index suitable for concurrent reads/writes if needed, e.g., IndexIDMap
        # self.index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        self.index = faiss.IndexFlatL2(dim) # Using basic IndexFlatL2 for now
        self.id_to_chunk = {}  # Maps FAISS vector id (usually sequential int) to original chunk_id (UUID)
        self.next_vector_id = 0 # Keep track of next available ID for IndexFlatL2

        # Load existing index and chunk map if they exist
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
        """Saves the FAISS index and the chunk ID map to disk."""
        try:
            logger.info(f"Saving FAISS index to {self.index_path}")
            faiss.write_index(self.index, self.index_path)
            # Save the chunk map
            chunk_map_path = self.index_path + ".chunks.npy"
            np.save(chunk_map_path, self.id_to_chunk)
            logger.info(f"FAISS index and chunk map saved successfully.")
        except Exception as e:
            logger.error(f"Error saving FAISS index or chunk map to {self.index_path}: {e}", exc_info=True)

    def load_index(self):
        """Loads the FAISS index and chunk ID map from disk if they exist."""
        if os.path.exists(self.index_path):
            try:
                logger.info(f"Loading FAISS index from {self.index_path}")
                self.index = faiss.read_index(self.index_path)
                self.next_vector_id = self.index.ntotal # Update next ID based on loaded index size
                # Load the chunk map
                chunk_map_path = self.index_path + ".chunks.npy"
                if os.path.exists(chunk_map_path):
                    self.id_to_chunk = np.load(chunk_map_path, allow_pickle=True).item()
                    logger.info(f"Loaded chunk map with {len(self.id_to_chunk)} entries.")
                else:
                    logger.warning(f"Chunk map file not found: {chunk_map_path}. Initializing empty map.")
                    self.id_to_chunk = {}
                logger.info(f"FAISS index loaded successfully. Index size: {self.index.ntotal}")
            except Exception as e:
                logger.error(f"Error loading FAISS index or chunk map from {self.index_path}: {e}. Reinitializing index.", exc_info=True)
                # Reinitialize if loading fails
                self.reset()
        else:
            logger.info(f"FAISS index file not found: {self.index_path}. Initializing new index.")
            # Initialize new index if file doesn't exist
            self.reset()

    def reset(self):
        """Resets the index and chunk map to an empty state."""
        logger.warning(f"Resetting FAISS index for path: {self.index_path}")
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_to_chunk = {}
        self.next_vector_id = 0
