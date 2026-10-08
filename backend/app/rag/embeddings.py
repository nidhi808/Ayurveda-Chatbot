import hashlib
import math
import numpy as np
from typing import List
from backend.app.config import GEMINI_API_KEY, EMBEDDING_MODEL

class EmbeddingService:
    """Provides vector embeddings using Gemini Embeddings API with local fallback."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = EMBEDDING_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self._is_legacy = False
        self.init_client()

    def init_client(self):
        """Initializes Gemini client using google.genai or legacy google.generativeai."""
        if not self.api_key:
            self.client = None
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self._is_legacy = False
        except Exception:
            try:
                import importlib
                genai_legacy = importlib.import_module("google.generativeai")
                genai_legacy.configure(api_key=self.api_key)
                self.client = genai_legacy
                self._is_legacy = True
            except Exception as e:
                print(f"[EmbeddingService] Warning initializing Gemini client: {e}")
                self.client = None

    def get_embedding(self, text: str) -> List[float]:
        """Fetches vector embedding for a single text string."""
        if self.client:
            try:
                if self._is_legacy:
                    # google.generativeai legacy API
                    import google.generativeai as _genai_legacy
                    response = _genai_legacy.embed_content(
                        model=f"models/{self.model_name}",
                        content=text
                    )
                    if response and "embedding" in response:
                        return list(response["embedding"])
                else:
                    # google.genai modern SDK
                    response = self.client.models.embed_content(
                        model=self.model_name,
                        contents=text
                    )
                    if response and hasattr(response, 'embedding') and hasattr(response.embedding, 'values'):
                        return list(response.embedding.values)
                    elif hasattr(response, 'embeddings') and len(response.embeddings) > 0:
                        return list(response.embeddings[0].values)
            except Exception as e:
                print(f"[EmbeddingService] Embedding API error: {e}")

        return self._local_dense_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Fetches vector embeddings for multiple text strings."""
        return [self.get_embedding(t) for t in texts]

    def _local_dense_embedding(self, text: str, dimension: int = 128) -> List[float]:
        """
        Fast, deterministic hash-based n-gram embedding vectorizer.
        Ensures local RAG functions even when offline or before GEMINI_API_KEY is supplied.
        """
        vec = np.zeros(dimension, dtype=np.float32)
        tokens = text.lower().replace("-", " ").split()

        for token in tokens:
            # Word-level hash
            idx = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % dimension
            vec[idx] += 1.0

            # 3-gram char hash for morphological & Sanskrit root sensitivity
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    sub = token[i:i+3]
                    sub_idx = int(hashlib.sha256(sub.encode('utf-8')).hexdigest(), 16) % dimension
                    vec[sub_idx] += 0.5

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

# Global embedding service
embedding_service = EmbeddingService()
