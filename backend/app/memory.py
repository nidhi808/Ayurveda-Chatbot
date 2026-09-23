import time
import uuid
from typing import Dict, List, Optional
from backend.app.models import MessageHistoryItem, SourceCitation

class ConversationMemory:
    """Stores in-memory conversation histories for multi-turn context."""

    def __init__(self, max_history_turns: int = 8):
        self.conversations: Dict[str, List[MessageHistoryItem]] = {}
        self.max_history_turns = max_history_turns

    def get_or_create_id(self, conversation_id: Optional[str]) -> str:
        if not conversation_id or conversation_id.strip() == "":
            return str(uuid.uuid4())
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[SourceCitation]] = None
    ) -> MessageHistoryItem:
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        item = MessageHistoryItem(
            role=role,
            content=content,
            timestamp=timestamp,
            sources=sources
        )
        self.conversations[conversation_id].append(item)

        # Keep history within reasonable window
        if len(self.conversations[conversation_id]) > self.max_history_turns * 2:
            self.conversations[conversation_id] = self.conversations[conversation_id][-(self.max_history_turns * 2):]

        return item

    def get_history(self, conversation_id: str) -> List[MessageHistoryItem]:
        return self.conversations.get(conversation_id, [])

    def format_history_for_prompt(self, conversation_id: str) -> str:
        """Formats prior exchanges into prompt context for multi-turn resolution."""
        history = self.get_history(conversation_id)
        if not history:
            return ""
        
        formatted = []
        for msg in history[:-1]:  # Exclude current question
            role_label = "User" if msg.role == "user" else "AyurBot"
            formatted.append(f"{role_label}: {msg.content}")
        
        return "\n".join(formatted)

# Global memory instance
memory_store = ConversationMemory()
