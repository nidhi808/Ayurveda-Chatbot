from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceCitation(BaseModel):
    id: str
    title: str
    category: str
    subcategory: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    source: str
    source_url: Optional[str] = None
    snippet: Optional[str] = None
    content: Optional[str] = None
    score: Optional[float] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Unique conversation session id")
    message: str = Field(..., min_length=1, description="User's query")
    category: Optional[str] = Field(None, description="Optional category filter (e.g. Doshas, Herbs, Lifestyle)")
    language: Optional[str] = Field("auto", description="Target language ('en', 'hi', 'sa', 'auto')")

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    sources: List[SourceCitation]
    category: Optional[str] = None
    language: Optional[str] = "en"
    safety_triggered: bool = False
    safety_reason: Optional[str] = None
    suggested_followups: Optional[List[str]] = None
    interpreted_query: Optional[str] = None
    corrected_terms: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None

class TranscribeResponse(BaseModel):
    text: str
    language: Optional[str] = "en"
    engine: str = "whisper.cpp"
    error: Optional[str] = None

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating or 1/-1 for up/down")
    feedback: Optional[str] = Field(None, description="Optional user commentary")

class FeedbackResponse(BaseModel):
    status: str
    message_id: str

class MessageHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: str
    sources: Optional[List[SourceCitation]] = None

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[MessageHistoryItem]

class DocumentChunk(BaseModel):
    id: str
    title: str
    category: str
    subcategory: Optional[str] = None
    content: str
    source: str
    source_url: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    language: str = "English"
    year: Optional[int] = None

class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    categories: List[str]

class EvaluationMetric(BaseModel):
    total_questions: int
    precision_at_k: float
    safety_detection_accuracy: float
    grounded_score: float
    details: List[Dict[str, Any]]
