import json
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


from backend.app.config import CORPUS_DIR
from backend.app.models import DocumentChunk
from backend.app.rag.vector_store import vector_store
from backend.app.rag.bm25_retriever import bm25_retriever

def load_and_index_corpus():
    """Reads all JSON corpus files and indexes them into VectorStore and BM25Retriever."""
    print("=" * 60)
    print("🌿 AyurBot Knowledge Base Ingestion Pipeline")
    print("=" * 60)

    if not CORPUS_DIR.exists():
        print(f"[Error] Corpus directory {CORPUS_DIR} not found.")
        return 0

    all_chunks = []
    corpus_files = list(CORPUS_DIR.glob("*.json"))
    print(f"Found {len(corpus_files)} corpus files in {CORPUS_DIR.name}/")

    for fpath in corpus_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        doc = DocumentChunk(**item)
                        all_chunks.append(doc)
            print(f"  ✓ Loaded {fpath.name}")
        except Exception as e:
            print(f"  ✗ Error loading {fpath.name}: {e}")

    print(f"\nTotal document chunks extracted: {len(all_chunks)}")

    # Index into Vector Store
    print("\n1. Indexing into Vector Store (Cosine Similarity)...")
    vector_store.add_documents(all_chunks)
    print("  ✓ Vector index saved to disk.")

    # Index into BM25
    print("\n2. Indexing into BM25 Keyword Engine...")
    bm25_retriever.index_documents(all_chunks)
    print("  ✓ BM25 index built successfully.")

    print("\n" + "=" * 60)
    print("🌿 Ingestion Complete! AyurBot knowledge base is ready.")
    print("=" * 60)
    return len(all_chunks)

if __name__ == "__main__":
    count = load_and_index_corpus()
    if count == 0:
        sys.exit(1)
