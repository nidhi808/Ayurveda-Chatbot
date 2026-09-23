import uuid
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI, HTTPException, Query, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import CORS_ORIGINS, GEMINI_MODEL, GEMINI_API_KEY
from backend.app.models import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    ConversationHistoryResponse,
    DocumentChunk,
    SourceCitation,
    EvaluationMetric,
    TranscribeResponse
)
from backend.app.safety import SafetyClassifier, MEDICAL_DISCLAIMER_TEXT
from backend.app.memory import memory_store
from backend.app.rag.hybrid_retriever import hybrid_retriever
from backend.app.rag.generator import rag_generator, RAGGenerator
from backend.app.rag.embeddings import embedding_service, EmbeddingService
from backend.app.rag.vector_store import vector_store
from backend.app.rag.evaluator import rag_evaluator
from backend.app.rag.transcriber import whisper_transcriber
from backend.app.rag.multilingual import detect_language, expand_multilingual_query
from backend.ingest import load_and_index_corpus

app = FastAPI(
    title="AyurBot API — AI-Powered Ayurveda Knowledge Assistant",
    description="Educational RAG API providing source-grounded Ayurveda explanations with dual-layer safety guardrails.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory feedback store
feedbacks_db: List[Dict[str, Any]] = []

@app.on_event("startup")
def startup_event():
    """Ensure vector store and BM25 index are loaded on startup."""
    if len(vector_store.chunks) == 0:
        print("[Startup] Loading and indexing Ayurveda corpus...")
        load_and_index_corpus()
    else:
        print(f"[Startup] Knowledge base ready with {len(vector_store.chunks)} document chunks.")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "product": "AyurBot",
        "chunks_indexed": len(vector_store.chunks),
        "gemini_configured": bool(rag_generator.api_key),
        "model": rag_generator.model_name
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    conversation_id = memory_store.get_or_create_id(request.conversation_id)
    message_id = str(uuid.uuid4())
    user_query = request.message.strip()

    if not user_query:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    # Detect or respect language preference
    lang = request.language
    if not lang or lang == "auto":
        lang = detect_language(user_query)

    # Record user message
    memory_store.add_message(conversation_id, role="user", content=user_query)

    # -------------------------------------------------------------
    # Layer 1: Input Safety Classifier
    # -------------------------------------------------------------
    is_safe, refusal_text, reason = SafetyClassifier.classify_input(user_query, lang=lang)
    if not is_safe:
        memory_store.add_message(conversation_id, role="assistant", content=refusal_text)
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            answer=refusal_text,
            sources=[],
            category=request.category,
            language=lang,
            safety_triggered=True,
            safety_reason=reason,
            suggested_followups=[
                "खोकल्यावर तुळशीचा वापर कसा करावा?",
                "त्रिदोष म्हणजे काय?",
                "दैनंदिन दिनचर्या कशी असावी?",
                "प्रकृती कशी ओळखावी?"
            ] if lang == "mr" else [
                "दिनचर्या क्या है?",
                "त्रिदोष क्या हैं?",
                "प्रकृति क्या होती है?",
                "तुलसी के क्या लाभ हैं?"
            ] if lang == "hi" else [
                "What is Dinacharya?",
                "What are the three doshas?",
                "What is Prakriti?",
                "What are the benefits of Tulsi?"
            ]
        )

    # -------------------------------------------------------------
    # Multi-turn Context Resolution
    # -------------------------------------------------------------
    history_context = memory_store.format_history_for_prompt(conversation_id)

    # -------------------------------------------------------------
    # Multilingual Query Expansion for Hybrid Retrieval
    # -------------------------------------------------------------
    retrieval_query = expand_multilingual_query(user_query)

    # -------------------------------------------------------------
    # Hybrid Retrieval (Vector + BM25 Fusion)
    # -------------------------------------------------------------
    citations = hybrid_retriever.retrieve(
        query=retrieval_query,
        top_k=4,
        category=request.category
    )

    # -------------------------------------------------------------
    # Grounded Generation & Layer 2 Output Validation
    # -------------------------------------------------------------
    raw_answer = rag_generator.generate(
        query=user_query,
        citations=citations,
        conversation_context=history_context,
        language=lang
    )

    final_answer = SafetyClassifier.validate_output(raw_answer)

    # Record assistant message with sources
    memory_store.add_message(
        conversation_id,
        role="assistant",
        content=final_answer,
        sources=citations
    )

    # Dynamic follow-up questions
    followups = _generate_followup_suggestions(user_query, citations, lang=lang)

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        answer=final_answer,
        sources=citations,
        category=request.category or (citations[0].category if citations else None),
        language=lang,
        safety_triggered=False,
        suggested_followups=followups
    )

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form("auto")
):
    """
    Transcribes audio input using whisper.cpp (pywhispercpp).
    Accepts audio file (WAV, MP3, WebM) and returns text and detected language.
    """
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file uploaded.")
        
        result = whisper_transcriber.transcribe_bytes(
            content,
            filename=file.filename or "recording.wav",
            language=language if language != "auto" else None
        )

        return TranscribeResponse(
            text=result.get("text", ""),
            language=result.get("language", language or "en"),
            engine="whisper.cpp",
            error=result.get("error")
        )
    except Exception as e:
        print(f"[API Transcribe] Error: {e}")
        return TranscribeResponse(
            text="",
            language=language or "en",
            engine="whisper.cpp",
            error=str(e)
        )

@app.get("/api/sources", response_model=List[SourceCitation])
def get_sources(category: Optional[str] = None):
    """Returns all or filtered knowledge sources available in the corpus."""
    results = []
    for c in vector_store.chunks:
        if category and category.lower() != "all" and c.get("category", "").lower() != category.lower():
            continue
        results.append(SourceCitation(
            id=c["id"],
            title=c["title"],
            category=c.get("category", "General"),
            subcategory=c.get("subcategory"),
            section=c.get("section"),
            page=c.get("page"),
            source=c.get("source", "Classical Ayurveda Reference"),
            source_url=c.get("source_url"),
            snippet=c.get("content", "")[:280] + "...",
            content=c.get("content", "")
        ))
    return results

@app.get("/api/sources/{doc_id}", response_model=SourceCitation)
def get_source_by_id(doc_id: str):
    """Retrieves full document details for a given source chunk."""
    for c in vector_store.chunks:
        if c["id"] == doc_id:
            return SourceCitation(
                id=c["id"],
                title=c["title"],
                category=c.get("category", "General"),
                subcategory=c.get("subcategory"),
                section=c.get("section"),
                page=c.get("page"),
                source=c.get("source", "Classical Ayurveda Reference"),
                source_url=c.get("source_url"),
                snippet=c.get("content", "")[:280] + "...",
                content=c.get("content", "")
            )
    raise HTTPException(status_code=404, detail=f"Source with id '{doc_id}' not found.")

@app.get("/api/categories")
def get_categories():
    """Returns unique categories and chunk counts."""
    counts: Dict[str, int] = {}
    for c in vector_store.chunks:
        cat = c.get("category", "Fundamentals")
        counts[cat] = counts.get(cat, 0) + 1
    
    categories = [
        {"name": "All", "count": len(vector_store.chunks)},
        *[{"name": k, "count": v} for k, v in sorted(counts.items())]
    ]
    return {"categories": categories}

@app.get("/api/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
def get_conversation_history(conversation_id: str):
    """Returns conversation message history."""
    messages = memory_store.get_history(conversation_id)
    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=messages
    )

@app.post("/api/feedback", response_model=FeedbackResponse)
def post_feedback(request: FeedbackRequest):
    """Records user feedback rating and comments."""
    feedback_entry = {
        "message_id": request.message_id,
        "rating": request.rating,
        "feedback": request.feedback
    }
    feedbacks_db.append(feedback_entry)
    return FeedbackResponse(status="success", message_id=request.message_id)

@app.get("/api/evaluate", response_model=EvaluationMetric)
def evaluate_endpoint(top_k: int = Query(3, ge=1, le=5)):
    """Runs automated evaluation suite against benchmark questions."""
    results = rag_evaluator.run_evaluation(top_k=top_k)
    return EvaluationMetric(**results)

@app.post("/api/config/gemini-key")
def configure_api_key(payload: Dict[str, str] = Body(...)):
    """Allows setting or updating Gemini API key dynamically from UI."""
    key = payload.get("api_key", "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty.")
    
    # Reinitialize services
    rag_generator.api_key = key
    rag_generator.init_client()
    embedding_service.api_key = key
    embedding_service.init_client()
    return {"status": "configured", "message": "Gemini API key updated successfully."}

def _generate_followup_suggestions(query: str, citations: List[SourceCitation], lang: str = "en") -> List[str]:
    """Generates 2-3 logical follow-up questions based on query and retrieved topics."""
    q_lower = query.lower()
    
    if lang == "mr":
        if any(w in q_lower or w in query for w in ["khokla", "खोकला", "कास", "कफ", "cough", "tulsi", "तुळस", "घसा"]):
            return [
                "खोकल्यावर तुळस आणि मधाचा उपयोग कसा करावा?",
                "खोकल्यासाठी ज्येष्ठमधाचे (Yashtimadhu) काय फायदे आहेत?",
                "कोरडा खोकला आणि कफयुक्त खोकला यावर कोणते आयुर्वेदिक उपाय आहेत?"
            ]
        elif any(w in q_lower or w in query for w in ["दोष", "वात", "पित्त", "कफ", "dosha", "tridosha"]):
            return [
                "वात आणि पित्त दोषांमध्ये काय फरक आहे?",
                "आपली शारीरिक प्रकृती कशी ओळखावी?",
                "कफ दोष संतुलित ठेवण्यासाठी कोणता आहार घ्यावा?"
            ]
        elif any(w in q_lower or w in query for w in ["दिनचर्या", "routine", "dinacharya"]):
            return [
                "ऋतुचर्या म्हणजे काय आणि ती दिनचर्येपेक्षा कशी वेगळी आहे?",
                "आयुर्वेदानुसार सकाळी उठल्यावर काय करावे?",
                "दुपारी झोपण्याबाबत आयुर्वेदात काय नियम आहेत?"
            ]
        elif any(w in q_lower or w in query for w in ["वनस्पती", "औषध", "तुळस", "अश्वगंधा", "त्रिफळा", "आवळा", "herb"]):
            return [
                "त्रिफळामध्ये कोणती तीन फळे असतात?",
                "अश्वगंधा घेण्याची योग्य वेळ आणि पद्धत कोणती?",
                "आवळ्याचे आरोग्यासाठी काय फायदे आहेत?"
            ]
        else:
            return [
                "पंचमहाभूते कोणती आहेत आणि त्यांचे महत्त्व काय?",
                "आयुर्वेदानुसार 'स्वस्थ' व्यक्तीची व्याख्या काय आहे?",
                "सप्त धातूंची शरीरातील मुख्य कार्ये कोणती आहेत?"
            ]

    if lang == "hi":
        if any(w in q_lower or w in query for w in ["khasi", "खांसी", "कफ", "cough", "tulsi", "तुलसी"]):
            return [
                "खांसी में तुलसी और शहद का उपयोग कैसे करें?",
                "मुलेठी (यष्टिमधु) के खांसी में क्या लाभ हैं?",
                "कफ को संतुलित करने के प्रमुख आयुर्वेदिक उपाय क्या हैं?"
            ]
        elif "दोष" in query or "वात" in query or "पित्त" in query or "कफ" in query:
            return [
                "वात और पित्त में क्या अंतर है?",
                "प्रकृति और त्रिदोष का क्या संबंध है?",
                "प्रत्येक दोष का मौसमी प्रकोप काल क्या है?"
            ]
        elif "दिनचर्या" in query:
            return [
                "ऋतुचर्या क्या है और यह दिनचर्या से कैसे भिन्न है?",
                "जिह्वा निर्लेखन (जीभ साफ करना) क्यों आवश्यक है?",
                "आयुर्वेद में दिन में सोने (दिवास्वप्न) पर क्या नियम हैं?"
            ]
        elif "तुलसी" in query or "अश्वगंधा" in query or "त्रिफला" in query:
            return [
                "त्रिफला में कौन से तीन फल होते हैं?",
                "अश्वगंधा के वैज्ञानिक प्रमाण क्या हैं?",
                "आमलकी के पाँच रस कौन से हैं?"
            ]
        else:
            return [
                "पंचमहाभूत क्या हैं?",
                "आयुर्वेद के अनुसार स्वस्थ व्यक्ति की परिभाषा क्या है?",
                "सप्त धातुएँ कौन-कौन सी हैं?"
            ]

    if "dosha" in q_lower or "vata" in q_lower or "pitta" in q_lower or "kapha" in q_lower:
        return [
            "What is the difference between Vata and Pitta?",
            "How does Prakriti relate to Tridosha?",
            "What are the seasonal peak times for each dosha?"
        ]
    elif "dinacharya" in q_lower or "routine" in q_lower:
        return [
            "What is Ritucharya and how does it differ from Dinacharya?",
            "Why is tongue scraping (Jihwa Nirlekhana) emphasized?",
            "What is the Ayurvedic view on daytime sleep?"
        ]
    elif "herb" in q_lower or "tulsi" in q_lower or "ashwagandha" in q_lower or "triphala" in q_lower:
        return [
            "What are the classical three fruits in Triphala?",
            "What does modern science say about Ashwagandha?",
            "What are the five tastes of Amalaki?"
        ]
    elif "agni" in q_lower or "ama" in q_lower:
        return [
            "What are the four clinical states of Jatharagni?",
            "What are the primary signs of Ama accumulation?",
            "What are incompatible food combinations (Viruddha Ahara)?"
        ]
    else:
        return [
            "What are the five Panchamahabhutas?",
            "What is the definition of health (Swastha) in Ayurveda?",
            "What are the seven Sapta Dhatus?"
        ]
