import React from "react";
import { Menu, BookOpen, Settings, BarChart3 } from "lucide-react";

export default function Header({
  sidebarOpen,
  setSidebarOpen,
  categories,
  selectedCategory,
  onSelectCategory,
  selectedLanguage,
  onSelectLanguage,
  onOpenExplorer,
  onOpenSettings,
  onOpenEvaluation,
  healthStatus
}) {
  const languages = [
    { code: "en", label: "English" },
    { code: "hi", label: "हिन्दी (Hindi / Hinglish)" },
    { code: "sa", label: "संस्कृतम् (Sanskrit)" },
    { code: "mr", label: "मराठी (Marathi)" },
    { code: "gu", label: "ગુજરાતી (Gujarati)" },
    { code: "ta", label: "தமிழ் (Tamil)" },
    { code: "te", label: "తెలుగు (Telugu)" },
    { code: "auto", label: "🌐 Auto-Detect" }
  ];

  return (
    <header className="top-navbar">
      <div className="navbar-left">
        <button
          className="toggle-sidebar-btn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title="Toggle Navigation"
        >
          <Menu size={18} />
        </button>

        <div className="category-bar">
          {categories.map((cat) => (
            <button
              key={cat.name}
              className={`category-pill ${selectedCategory === cat.name ? "active" : ""}`}
              onClick={() => onSelectCategory(cat.name)}
            >
              <span>{cat.name}</span>
              {cat.count !== undefined && (
                <span className="pill-count">{cat.count}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="navbar-right">
        {/* Language Switcher */}
        <select
          value={selectedLanguage}
          onChange={(e) => onSelectLanguage(e.target.value)}
          className="nav-action-btn"
          style={{ cursor: "pointer", outline: "none", background: "#fbfdfb" }}
          title="Choose conversation language"
        >
          {languages.map((l) => (
            <option key={l.code} value={l.code}>
              {l.label}
            </option>
          ))}
        </select>

        <div className="status-indicator">
          <div className="status-dot" style={{ backgroundColor: healthStatus ? "#2b9348" : "#d94826" }} />
          <span>{healthStatus ? "RAG Active" : "Connecting..."}</span>
        </div>

        <button
          className="nav-action-btn"
          onClick={onOpenExplorer}
          title="Explore Knowledge Corpus"
        >
          <BookOpen size={15} />
          <span>Corpus</span>
        </button>

        <button
          className="nav-action-btn"
          onClick={onOpenEvaluation}
          title="View RAG Evaluation Benchmark"
        >
          <BarChart3 size={15} />
          <span>Evaluation</span>
        </button>

        <button
          className="nav-action-btn"
          onClick={onOpenSettings}
          title="Gemini API & System Settings"
        >
          <Settings size={15} />
        </button>
      </div>
    </header>
  );
}
