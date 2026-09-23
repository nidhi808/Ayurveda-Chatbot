import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from backend.app.models import DocumentChunk

class BM25Retriever:
    """Keyword search engine using BM25 for precise Ayurvedic terminology matching."""

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    STOPWORDS = {
        "what", "is", "are", "the", "a", "an", "and", "or", "in", "of", "to", "for", 
        "with", "on", "at", "by", "from", "as", "into", "its", "it", "this", "that", 
        "which", "who", "whom", "can", "how", "explain", "describe", "about"
    }

    def tokenize(self, text: str) -> List[str]:
        """Cleans and tokenizes text for keyword matching, handling Sanskrit plurals and stopwords."""
        text_clean = re.sub(r"[^\w\s]", " ", text.lower())
        raw_tokens = text_clean.split()
        tokens = []
        for t in raw_tokens:
            if len(t) <= 1 or t in self.STOPWORDS:
                continue
            tokens.append(t)
            # Add stem variant if ends with 's' or 'as' for Sanskrit plurals
            if t.endswith("as") and len(t) > 4:
                tokens.append(t[:-1]) # e.g. panchamahabhutas -> panchamahabhuta
            elif t.endswith("s") and len(t) > 3:
                tokens.append(t[:-1]) # e.g. doshas -> dosha
        return tokens

    def index_documents(self, documents: List[DocumentChunk]):
        """Builds BM25 index over documents."""
        self.chunks = []
        self.corpus_tokens = []

        for doc in documents:
            chunk_dict = doc.model_dump()
            self.chunks.append(chunk_dict)
            text_to_index = f"{doc.title} {doc.category} {doc.subcategory or ''} {doc.content}"
            tokens = self.tokenize(text_to_index)
            self.corpus_tokens.append(tokens)

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Searches BM25 index and returns scored chunks."""
        if not self.bm25 or len(self.chunks) == 0:
            return []

        q_tokens = self.tokenize(query)
        if not q_tokens:
            return []

        scores = self.bm25.get_scores(q_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0:
                continue

            chunk = self.chunks[idx].copy()
            if category and category.lower() != "all":
                if chunk.get("category", "").lower() != category.lower():
                    continue

            chunk["score"] = score
            results.append(chunk)

            if len(results) >= top_k:
                break

        return results

# Global BM25 retriever
bm25_retriever = BM25Retriever()
