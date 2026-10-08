import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from backend.app.config import INDEX_DIR
from backend.app.models import DocumentChunk
from backend.app.rag.embeddings import embedding_service

class VectorStore:
    """Stores document vectors and executes Cosine Similarity search."""

    def __init__(self, index_path: Path = INDEX_DIR / "vector_index.json"):
        self.index_path = index_path
        self.chunks: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.empty((0, 0))
        self.load()

    def add_documents(self, documents: List[DocumentChunk]):
        """Embeds and indexes document chunks."""
        self.chunks = []
        vectors_list = []

        texts = [f"{d.title}\n{d.category}\n{d.content}" for d in documents]
        embeddings = embedding_service.get_embeddings_batch(texts)

        for doc, emb in zip(documents, embeddings):
            chunk_data = doc.model_dump()
            self.chunks.append(chunk_data)
            vectors_list.append(emb)

        if vectors_list:
            self.vectors = np.array(vectors_list, dtype=np.float32)
            # Ensure row-wise L2 normalization for rapid cosine distance dot product
            norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.vectors = self.vectors / norms

        self.save()

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Searches index for top_k most similar chunks matching category filter."""
        if len(self.chunks) == 0 or self.vectors.size == 0:
            return []

        query_vec = np.array(embedding_service.get_embedding(query), dtype=np.float32)
        if self.vectors.ndim == 2 and self.vectors.size > 0 and self.vectors.shape[1] != query_vec.shape[0]:
            print(f"[VectorStore] Embedding dimension mismatch ({self.vectors.shape[1]} vs {query_vec.shape[0]}). Re-indexing corpus with active embedding model...")
            from backend.ingest import load_and_index_corpus
            load_and_index_corpus()

        q_norm = np.linalg.norm(query_vec)
        if q_norm > 0:
            query_vec = query_vec / q_norm

        # Cosine similarity dot product
        similarities = np.dot(self.vectors, query_vec)

        # Rank indices
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices:
            chunk = self.chunks[idx].copy()
            # Category filter (case-insensitive)
            if category and category.lower() != "all":
                if chunk.get("category", "").lower() != category.lower():
                    continue

            chunk["score"] = float(similarities[idx])
            results.append(chunk)

            if len(results) >= top_k:
                break

        return results

    def save(self):
        """Persists chunks and vectors to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": self.chunks,
            "vectors": self.vectors.tolist() if self.vectors.size > 0 else []
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        """Loads chunks and vectors from disk if exists."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    vec_list = data.get("vectors", [])
                    if vec_list:
                        self.vectors = np.array(vec_list, dtype=np.float32)
                
                # Also ensure BM25 index is populated
                if self.chunks:
                    from backend.app.rag.bm25_retriever import bm25_retriever
                    doc_objs = [DocumentChunk(**c) for c in self.chunks]
                    bm25_retriever.index_documents(doc_objs)
            except Exception as e:
                print(f"[VectorStore] Error loading index: {e}")
                self.chunks = []
                self.vectors = np.empty((0, 0))

# Global vector store
vector_store = VectorStore()
