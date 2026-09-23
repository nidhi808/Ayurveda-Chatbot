import React from "react";
import { X, ExternalLink, BookOpen, Layers, Bookmark } from "lucide-react";

export default function SourceViewer({ source, onClose }) {
  if (!source) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: "#eef6f0",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#2d6a4f"
              }}
            >
              <BookOpen size={18} />
            </div>
            <div>
              <div style={{ fontSize: "11px", fontWeight: "700", textTransform: "uppercase", color: "#c9933b", letterSpacing: "0.5px" }}>
                {source.category} {source.subcategory ? `• ${source.subcategory}` : ""}
              </div>
              <h3 className="modal-title" style={{ fontSize: "18px" }}>{source.title}</h3>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-content">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "12px",
              background: "#f7faf7",
              padding: "14px",
              borderRadius: "12px",
              border: "1px solid #e1ebe3",
              marginBottom: "20px"
            }}
          >
            <div>
              <div style={{ fontSize: "11px", color: "#718579" }}>Authoritative Source</div>
              <div style={{ fontSize: "13px", fontWeight: "600", color: "#1c2826" }}>{source.source}</div>
            </div>
            {source.section && (
              <div>
                <div style={{ fontSize: "11px", color: "#718579" }}>Section / Chapter</div>
                <div style={{ fontSize: "13px", fontWeight: "600", color: "#1c2826" }}>{source.section}</div>
              </div>
            )}
            {source.page && (
              <div>
                <div style={{ fontSize: "11px", color: "#718579" }}>Page Reference</div>
                <div style={{ fontSize: "13px", fontWeight: "600", color: "#1c2826" }}>Page {source.page}</div>
              </div>
            )}
            {source.score && (
              <div>
                <div style={{ fontSize: "11px", color: "#718579" }}>RRF Relevance Score</div>
                <div style={{ fontSize: "13px", fontWeight: "600", color: "#2d6a4f" }}>{source.score}</div>
              </div>
            )}
          </div>

          <div style={{ marginBottom: "16px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#2d6a4f", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              <Layers size={15} />
              <span>Full Indexed Passage</span>
            </h4>
            <div
              style={{
                fontSize: "14.5px",
                lineHeight: "1.75",
                color: "#293831",
                background: "#ffffff",
                border: "1px solid #e6ede8",
                padding: "18px",
                borderRadius: "12px",
                whiteSpace: "pre-line"
              }}
            >
              {source.content || source.snippet}
            </div>
          </div>

          {source.source_url && (
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <a
                href={source.source_url}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "13px",
                  color: "#2d6a4f",
                  fontWeight: "600",
                  textDecoration: "none",
                  background: "#edf5ef",
                  padding: "8px 14px",
                  borderRadius: "8px"
                }}
              >
                <span>Visit Official AYUSH Portal</span>
                <ExternalLink size={14} />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
