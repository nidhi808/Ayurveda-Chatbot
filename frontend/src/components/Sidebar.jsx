import React from "react";
import { Plus, MessageSquare, Database, AlertCircle, X, Trash2 } from "lucide-react";

export default function Sidebar({
  sidebarOpen,
  setSidebarOpen,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  chunkCount
}) {
  return (
    <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <div className="brand-wrapper">
          <div className="brand-logo-icon">🌿</div>
          <div className="brand-text-col">
            <h1 className="brand-title">AyurBot</h1>
            <div className="brand-subtitle">Knowledge Assistant</div>
          </div>
        </div>
        <button
          className="toggle-sidebar-btn"
          style={{ display: "none" }}
          onClick={() => setSidebarOpen(false)}
        >
          <X size={18} color="#ffffff" />
        </button>
      </div>

      <button className="btn-new-chat" onClick={onNewChat}>
        <Plus size={16} />
        <span>New Conversation</span>
      </button>

      <div className="sidebar-content">
        <div>
          <div className="sidebar-section-title">Conversations</div>
          {conversations.length === 0 ? (
            <div style={{ padding: "8px 12px", fontSize: "12px", color: "#6e897d" }}>
              No previous chats yet
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`conversation-item ${conv.id === activeConversationId ? "active" : ""}`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                  <MessageSquare size={14} style={{ flexShrink: 0 }} />
                  <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {conv.title || "Ayurvedic Inquiry"}
                  </span>
                </div>
                <button
                  className="icon-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  title="Delete chat"
                  style={{ color: "#7a9488" }}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))
          )}
        </div>

        <div className="corpus-stat-card">
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", fontWeight: "700", color: "#ffffff" }}>
            <Database size={14} color="#c9933b" />
            <span>Knowledge Corpus</span>
          </div>
          <div className="stat-row">
            <span>Indexed Chunks</span>
            <span className="stat-badge">{chunkCount || 28}</span>
          </div>
          <div className="stat-row">
            <span>Primary Sources</span>
            <span>AYUSH & CCRAS</span>
          </div>
          <div className="stat-row">
            <span>Retrieval Engine</span>
            <span>Vector + BM25</span>
          </div>
        </div>

        <div className="disclaimer-card">
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: "700", marginBottom: "4px" }}>
            <AlertCircle size={14} />
            <span>Educational Use</span>
          </div>
          AyurBot provides classical Ayurvedic concepts & modern scientific literature. It does not diagnose or prescribe medicine.
        </div>
      </div>

      <div className="sidebar-footer">
        <div style={{ fontSize: "11px", color: "#6e897d", textAlign: "center" }}>
          प्राचीन ज्ञान • आधुनिक अनुसंधान<br />
          v1.0.0 Powered by Gemini & RAG
        </div>
      </div>
    </aside>
  );
}
