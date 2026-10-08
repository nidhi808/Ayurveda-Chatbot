from typing import List, Dict, Any, Optional
from backend.app.rag.vector_store import vector_store
from backend.app.rag.bm25_retriever import bm25_retriever
from backend.app.models import SourceCitation, DocumentChunk

class HybridRetriever:
    """Fuses Vector Semantic Search and BM25 Keyword Search using Reciprocal Rank Fusion."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None
    ) -> List[SourceCitation]:
        """
        Executes hybrid search combining vector similarity and BM25 rankings.
        """
        candidate_k = max(30, top_k * 6)
        # Search global candidate pool so queries targeting other classical domains are never dropped
        vector_results = vector_store.search(query, top_k=candidate_k, category=None)
        bm25_results = bm25_retriever.search(query, top_k=candidate_k, category=None)

        # Relevance guardrail: if query has 0 BM25 match and weak vector similarity,
        # attempt fallback search with canonical Ayurveda entities recognized in the query
        max_bm25 = max([item.get("score", 0) for item in bm25_results], default=0.0)
        max_vector = max([item.get("score", 0) for item in vector_results], default=0.0)
        if max_bm25 == 0.0 and max_vector < 0.36:
            try:
                from backend.app.rag.spelling import spell_corrector
                res = spell_corrector.process_query(query)
                if res.canonical_terms:
                    fallback_query = " ".join(res.canonical_terms)
                    vector_results = vector_store.search(fallback_query, top_k=candidate_k, category=None)
                    bm25_results = bm25_retriever.search(fallback_query, top_k=candidate_k, category=None)
                    max_bm25 = max([item.get("score", 0) for item in bm25_results], default=0.0)
                    max_vector = max([item.get("score", 0) for item in vector_results], default=0.0)
                    if max_bm25 == 0.0 and max_vector < 0.20:
                        return []
                else:
                    return []
            except Exception:
                return []

        # Reciprocal Rank Fusion (RRF) with balanced weights & category prioritization boost
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        has_category_filter = bool(category and category.lower() != "all")
        target_cat = category.lower() if has_category_filter else ""

        for rank, item in enumerate(vector_results, 1):
            doc_id = item["id"]
            doc_map[doc_id] = item
            base_score = 1.0 / (self.rrf_k + rank)
            # Prioritize documents matching the active category
            if has_category_filter and item.get("category", "").lower() == target_cat:
                base_score *= 1.35
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + base_score

        for rank, item in enumerate(bm25_results, 1):
            doc_id = item["id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = item
            # Boost exact keyword matches significantly for classical domain terms
            base_score = (1.0 / (self.rrf_k + rank)) * 1.5
            if has_category_filter and item.get("category", "").lower() == target_cat:
                base_score *= 1.35
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + base_score

        # Rank by fused score
        sorted_ids = sorted(doc_scores.keys(), key=lambda d_id: doc_scores[d_id], reverse=True)

        final_citations: List[SourceCitation] = []
        for doc_id in sorted_ids[:top_k]:
            data = doc_map[doc_id]
            fused_score = doc_scores[doc_id]
            full_text = data.get("content", "")
            snippet = full_text[:280] + "..." if len(full_text) > 280 else full_text

            citation = SourceCitation(
                id=data["id"],
                title=data.get("title", "Ayurvedic Knowledge Reference"),
                category=data.get("category", "General"),
                subcategory=data.get("subcategory"),
                section=data.get("section"),
                page=data.get("page"),
                source=data.get("source", "Classical Ayurveda Reference"),
                source_url=data.get("source_url"),
                snippet=snippet,
                content=full_text,
                score=round(fused_score, 4)
            )
            final_citations.append(citation)

        return final_citations

# Global hybrid retriever
hybrid_retriever = HybridRetriever()
