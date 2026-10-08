import React, { useState } from "react";
import { BookOpen, Copy, Check, ThumbsUp, ThumbsDown, ShieldAlert, Sparkles, ChevronDown, ChevronUp, Image as ImageIcon } from "lucide-react";
import { submitFeedback } from "../api";

export default function ChatMessage({ message, onSelectSource, onSelectFollowup }) {
  const [copied, setCopied] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const [feedbackGiven, setFeedbackGiven] = useState(null); // 'up' | 'down'

  const isUser = message.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (type) => {
    setFeedbackGiven(type);
    if (message.id) {
      await submitFeedback({
        message_id: message.id,
        rating: type === "up" ? 5 : 1,
        feedback: type === "up" ? "Helpful response" : "Needs improvement"
      });
    }
  };

  if (isUser) {
    return (
      <div className="message-row user">
        <div className="user-bubble">{message.content}</div>
      </div>
    );
  }

  // Helper to format basic markdown-like structures into clean HTML
  const formatBody = (text) => {
    if (!text) return null;
    const lines = text.split("\n");
    const blocks = [];
    let currentList = [];
    let currentOrderedList = [];

    const flushList = () => {
      if (currentList.length > 0) {
        blocks.push({ type: "list", items: [...currentList] });
        currentList = [];
      }
      if (currentOrderedList.length > 0) {
        blocks.push({ type: "ordered-list", items: [...currentOrderedList] });
        currentOrderedList = [];
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) {
        flushList();
        continue;
      }
      if (line.startsWith("## ")) {
        flushList();
        blocks.push({ type: "h2", content: line.replace(/^##\s+/, "") });
      } else if (line.startsWith("### ")) {
        flushList();
        blocks.push({ type: "h3", content: line.replace(/^###\s+/, "") });
      } else if (line.startsWith("#### ")) {
        flushList();
        blocks.push({ type: "h4", content: line.replace(/^####\s+/, "") });
      } else if (line.startsWith("• ") || line.startsWith("- ") || line.startsWith("* ")) {
        if (currentOrderedList.length > 0) flushList();
        currentList.push(line.replace(/^[•\-\*]\s*/, ""));
      } else if (/^\d+\.\s/.test(line)) {
        if (currentList.length > 0) flushList();
        currentOrderedList.push(line.replace(/^\d+\.\s*/, ""));
      } else {
        flushList();
        blocks.push({ type: "p", content: line });
      }
    }
    flushList();

    return blocks.map((b, idx) => {
      if (b.type === "h2") return <h2 key={idx} style={{ fontSize: "17px", fontWeight: "700", margin: "14px 0 6px", color: "#143828" }}>{b.content}</h2>;
      if (b.type === "h3") return <h3 key={idx}>{b.content}</h3>;
      if (b.type === "h4") return <h4 key={idx}>{b.content}</h4>;
      if (b.type === "list") {
        return (
          <ul key={idx}>
            {b.items.map((it, itIdx) => (
              <li key={itIdx} dangerouslySetInnerHTML={{ __html: parseBold(it) }} />
            ))}
          </ul>
        );
      }
      if (b.type === "ordered-list") {
        return (
          <ol key={idx}>
            {b.items.map((it, itIdx) => (
              <li key={itIdx} dangerouslySetInnerHTML={{ __html: parseBold(it) }} />
            ))}
          </ol>
        );
      }
      return <p key={idx} dangerouslySetInnerHTML={{ __html: parseBold(b.content) }} />;
    });
  };

  const parseBold = (str) => {
    return str
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>");
  };

  return (
    <div className="message-row bot">
      <div className="bot-card">
        <div className="bot-header-meta">
          <div className="bot-badge-title">
            <Sparkles size={16} color="#2d6a4f" />
            <span>AyurBot Grounded Knowledge</span>
          </div>
          {message.category && (
            <span className="bot-category-tag">{message.category}</span>
          )}
        </div>

        {message.safety_triggered && (
          <div className="safety-callout">
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700", marginBottom: "4px" }}>
              <ShieldAlert size={18} color="#d94826" />
              <span>Medical Safety Notice</span>
            </div>
            AyurBot detected a query seeking clinical diagnosis, emergency triage, or prescription. For your safety, the request was educationalized.
          </div>
        )}

        {message.interpreted_query && (
          <div className="interpreted-callout">
            <Sparkles size={14} color="#2d6a4f" style={{ flexShrink: 0 }} />
            <span>Understood topic: <strong>{message.interpreted_query}</strong></span>
          </div>
        )}

        <div className="bot-body-text">{formatBody(message.content)}</div>

        {/* Botanical Herb / Concept Image Card */}
        {message.image && (
          <div className="herb-image-card">
            <div className="herb-image-container">
              <img
                src={message.image.url}
                alt={message.image.title}
                className="herb-image-preview"
                loading="lazy"
              />
              <div className="herb-image-badge">
                <ImageIcon size={13} />
                <span>Botanical Reference</span>
              </div>
            </div>
            <div className="herb-image-details">
              <div className="herb-image-title">{message.image.title}</div>
              {message.image.botanical && (
                <div className="herb-image-botanical">{message.image.botanical}</div>
              )}
              {message.image.caption && (
                <div className="herb-image-caption">{message.image.caption}</div>
              )}
            </div>
          </div>
        )}

        {/* Sources Accordion */}
        {message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <div
              className="sources-header-bar"
              onClick={() => setSourcesOpen(!sourcesOpen)}
            >
              <div className="sources-title">
                <BookOpen size={15} />
                <span>Verified Sources ({message.sources.length})</span>
              </div>
              {sourcesOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {sourcesOpen && (
              <div className="sources-chips-grid">
                {message.sources.map((src, idx) => (
                  <div
                    key={src.id || idx}
                    className="source-chip"
                    onClick={() => onSelectSource(src)}
                    title="Click to view complete citation text"
                  >
                    <div className="source-chip-title">{src.title}</div>
                    <div className="source-chip-meta">
                      <span>📚 {src.source}</span>
                      {src.page && <span>• p. {src.page}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="bot-action-bar">
          <div style={{ fontSize: "11px", color: "#8a9e94" }}>
            {message.sources && message.sources.length > 0
              ? `Grounded from ${message.sources.length} document citations`
              : "Educational knowledge guidance"}
          </div>

          <div className="action-buttons">
            <button
              className="icon-btn"
              onClick={handleCopy}
              title="Copy to clipboard"
            >
              {copied ? <Check size={14} color="#2b9348" /> : <Copy size={14} />}
            </button>
            <button
              className={`icon-btn ${feedbackGiven === "up" ? "active" : ""}`}
              onClick={() => handleFeedback("up")}
              title="Helpful response"
            >
              <ThumbsUp size={14} />
            </button>
            <button
              className={`icon-btn ${feedbackGiven === "down" ? "active" : ""}`}
              onClick={() => handleFeedback("down")}
              title="Needs improvement"
            >
              <ThumbsDown size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Suggested Follow-up Questions */}
      {message.suggested_followups && message.suggested_followups.length > 0 && (
        <div className="followups-wrapper">
          {message.suggested_followups.map((q, idx) => (
            <button
              key={idx}
              className="followup-chip"
              onClick={() => onSelectFollowup(q)}
            >
              <span>{q}</span>
              <span>→</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
