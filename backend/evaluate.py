import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.ingest import load_and_index_corpus
from backend.app.rag.vector_store import vector_store
from backend.app.rag.bm25_retriever import bm25_retriever
from backend.app.rag.evaluator import rag_evaluator

def main():
    print("=" * 65)
    print("🌿 AyurBot RAG Evaluation Benchmark Suite")
    print("=" * 65)

    if len(vector_store.chunks) == 0:
        print("Knowledge base index not detected in memory, re-indexing...")
        load_and_index_corpus()

    print("\nRunning benchmark on evaluation questions dataset...")
    results = rag_evaluator.run_evaluation(top_k=3)

    print("-" * 65)
    print(f"Total Test Questions Evaluated : {results['total_questions']}")
    print(f"Retrieval Precision@3          : {results['precision_at_k']}%")
    print(f"Safety Detection Accuracy      : {results['safety_detection_accuracy']}%")
    print(f"Overall Grounded Score         : {results['grounded_score']}%")
    print("-" * 65)

    print("\nItemized Breakdown:")
    for d in results["details"]:
        status_icon = "✓" if d["passed"] else "✗"
        print(f"  [{status_icon}] [{d['category']}] Q: {d['question'][:55]}...")
        if d["type"] == "safety_check":
            print(f"      -> Safety Trigger Intercepted: Reason={d.get('reason')}")
        else:
            print(f"      -> Sources: {d.get('retrieved_sources_count')}, Matched Keywords: {d.get('expected_keywords_matched')}")

    print("\n" + "=" * 65)
    print("Evaluation Complete!")
    print("=" * 65)

if __name__ == "__main__":
    main()
