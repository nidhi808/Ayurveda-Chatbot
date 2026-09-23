import React, { useState, useEffect } from "react";
import { X, Search, BookOpen, ExternalLink, Filter } from "lucide-react";
import { fetchSources } from "../api";

export default function KnowledgeExplorer({ onClose, onSelectTopic }) {
  const [sources, setSources] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await fetchSources();
      setSources(data);
      setLoading(false);
    }
    load();
  }, []);

  const categories = ["All", "Fundamentals", "Doshas", "Lifestyle", "Herbs", "Traditional Concepts"];

  const filtered = sources.filter((item) => {
    const matchesCat = selectedFilter === "All" || item.category === selectedFilter;
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.source?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "800px" }} onClick={(e) => e.stopPropagation()}>
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
              <h3 className="modal-title">Knowledge Corpus Explorer</h3>
              <div style={{ fontSize: "12px", color: "#6d8276" }}>
                Browse authentic documents, classical references, and herb monographs ({sources.length} total)
              </div>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-content" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Search bar & filter pills */}
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: "#f4f7f4",
                padding: "8px 14px",
                borderRadius: "10px",
                border: "1px solid #dbe6de"
              }}
            >
              <Search size={16} color="#758c7f" />
              <input
                type="text"
                placeholder="Search corpus (e.g., Pitta, Dinacharya, Tulsi, Charaka)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  border: "none",
                  outline: "none",
                  background: "transparent",
                  width: "100%",
                  fontSize: "14px"
                }}
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {categories.map((cat) => (
              <button
                key={cat}
                className={`category-pill ${selectedFilter === cat ? "active" : ""}`}
                style={{ fontSize: "12px", padding: "4px 12px" }}
                onClick={() => setSelectedFilter(cat)}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Document list */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", overflowY: "auto", maxHeight: "480px" }}>
            {loading ? (
              <div style={{ padding: "40px", textAlign: "center", color: "#778d81" }}>
                Loading knowledge corpus...
              </div>
            ) : filtered.length === 0 ? (
              <div style={{ padding: "40px", textAlign: "center", color: "#778d81" }}>
                No documents matched your query.
              </div>
            ) : (
              filtered.map((item) => (
                <div
                  key={item.id}
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e1ebe3",
                    borderRadius: "12px",
                    padding: "16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                    transition: "all 0.15s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: "700",
                          textTransform: "uppercase",
                          color: "#c9933b",
                          letterSpacing: "0.5px"
                        }}
                      >
                        {item.category} {item.subcategory ? `• ${item.subcategory}` : ""}
                      </span>
                      <h4 style={{ fontSize: "15px", fontWeight: "700", color: "#143828", marginTop: "2px" }}>
                        {item.title}
                      </h4>
                    </div>

                    <button
                      className="nav-action-btn"
                      style={{ fontSize: "11px", padding: "4px 8px" }}
                      onClick={() => {
                        onSelectTopic(item.title, item.category);
                        onClose();
                      }}
                    >
                      Ask About This →
                    </button>
                  </div>

                  <p style={{ fontSize: "13.5px", color: "#485951", lineHeight: "1.6" }}>
                    {item.content?.slice(0, 260)}...
                  </p>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11.5px", color: "#7a9184", borderTop: "1px solid #edf2ee", paddingTop: "8px" }}>
                    <span>📚 {item.source} {item.section ? `• ${item.section}` : ""}</span>
                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ display: "flex", alignItems: "center", gap: "4px", color: "#2d6a4f", textDecoration: "none", fontWeight: "600" }}
                      >
                        <span>Portal</span>
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
