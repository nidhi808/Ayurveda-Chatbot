import json
from pathlib import Path
from typing import Dict, Any, List
from backend.app.config import DATA_DIR
from backend.app.safety import SafetyClassifier
from backend.app.rag.hybrid_retriever import hybrid_retriever
from backend.app.rag.generator import rag_generator

class RAGEvaluator:
    """Evaluates RAG retrieval precision, grounding, and safety classification."""

    def __init__(self, eval_path: Path = DATA_DIR / "evaluation_questions.json"):
        self.eval_path = eval_path

    def run_evaluation(self, top_k: int = 3) -> Dict[str, Any]:
        """Runs automated evaluation suite against benchmark questions."""
        if not self.eval_path.exists():
            return {
                "error": "Evaluation dataset not found",
                "total_questions": 0
            }

        with open(self.eval_path, "r", encoding="utf-8") as f:
            questions: List[Dict[str, Any]] = json.load(f)

        total = len(questions)
        safety_correct = 0
        safety_total = 0
        retrieval_hits = 0
        non_safety_total = 0
        detailed_results = []

        for item in questions:
            q_id = item["id"]
            category = item["category"]
            question = item["question"]
            is_safety = item.get("is_safety_trigger", False)
            expected_keywords = item.get("expected_keywords", [])

            # Step 1: Test Safety Classifier
            is_safe, refusal, reason = SafetyClassifier.classify_input(question)

            if is_safety:
                safety_total += 1
                # Expected to be intercepted (not safe)
                passed = (not is_safe)
                if passed:
                    safety_correct += 1
                
                detailed_results.append({
                    "id": q_id,
                    "category": category,
                    "question": question,
                    "type": "safety_check",
                    "passed": passed,
                    "reason": reason
                })
            else:
                non_safety_total += 1
                # Normal query: Test hybrid retrieval and generation
                citations = hybrid_retriever.retrieve(question, top_k=top_k)
                answer = rag_generator.generate(question, citations)

                # Check if any expected keyword is present in retrieved chunks or answer
                retrieved_text = " ".join([f"{c.title} {c.content or c.snippet or ''}" for c in citations]).lower()
                keyword_hits = [kw for kw in expected_keywords if kw.lower() in retrieved_text or kw.lower() in answer.lower()]
                hit = len(keyword_hits) > 0

                if hit:
                    retrieval_hits += 1

                detailed_results.append({
                    "id": q_id,
                    "category": category,
                    "question": question,
                    "type": "retrieval_precision",
                    "retrieved_sources_count": len(citations),
                    "expected_keywords_matched": keyword_hits,
                    "passed": hit
                })

        precision_at_k = (retrieval_hits / non_safety_total) if non_safety_total > 0 else 0.0
        safety_accuracy = (safety_correct / safety_total) if safety_total > 0 else 0.0
        overall_grounded_score = ((retrieval_hits + safety_correct) / total) if total > 0 else 0.0

        return {
            "total_questions": total,
            "precision_at_k": round(precision_at_k * 100, 2),
            "safety_detection_accuracy": round(safety_accuracy * 100, 2),
            "grounded_score": round(overall_grounded_score * 100, 2),
            "details": detailed_results
        }

# Global evaluator instance
rag_evaluator = RAGEvaluator()
