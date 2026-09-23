import React, { useState } from "react";
import { X, Key, Check, AlertTriangle, ShieldCheck } from "lucide-react";
import { configureGeminiKey } from "../api";

export default function SettingsModal({ onClose, currentModel }) {
  const [apiKey, setApiKey] = useState("");
  const [statusMsg, setStatusMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await configureGeminiKey(apiKey.trim());
      setStatusMsg({ type: "success", text: res.message || "Key configured successfully!" });
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setStatusMsg({ type: "error", text: err.message || "Failed to update API key" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "520px" }} onClick={(e) => e.stopPropagation()}>
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
              <Key size={18} />
            </div>
            <div>
              <h3 className="modal-title">Settings & LLM Configuration</h3>
              <div style={{ fontSize: "12px", color: "#6d8276" }}>
                Manage Gemini API and generation parameters
              </div>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form className="modal-content" onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "600", color: "#143828", marginBottom: "6px" }}>
              Google Gemini API Key
            </label>
            <input
              type="password"
              placeholder="AIzaSy..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "10px",
                border: "1px solid #d2ded5",
                fontSize: "14px",
                outline: "none"
              }}
            />
            <div style={{ fontSize: "11px", color: "#7a9184", marginTop: "4px" }}>
              Stored locally in server runtime session. Keys are never logged or exposed.
            </div>
          </div>

          <div
            style={{
              background: "#f7faf7",
              border: "1px solid #e1ebe3",
              borderRadius: "10px",
              padding: "12px 14px",
              fontSize: "12.5px",
              color: "#3f5449",
              display: "flex",
              flexDirection: "column",
              gap: "4px"
            }}
          >
            <div><strong>Active Model:</strong> {currentModel || "gemini-2.5-flash"}</div>
            <div><strong>Embeddings:</strong> Gemini Embeddings with Local Dense Fallback</div>
            <div><strong>Dual Guardrails:</strong> Active (Layer 1 Input + Layer 2 Output)</div>
          </div>

          {statusMsg && (
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "8px",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                background: statusMsg.type === "success" ? "#d8eedc" : "#fde2e2",
                color: statusMsg.type === "success" ? "#1b632e" : "#b02a2a"
              }}
            >
              {statusMsg.type === "success" ? <ShieldCheck size={16} /> : <AlertTriangle size={16} />}
              <span>{statusMsg.text}</span>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
            <button
              type="button"
              className="nav-action-btn"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-new-chat"
              style={{ margin: 0, padding: "8px 20px" }}
              disabled={loading || !apiKey.trim()}
            >
              {loading ? "Updating..." : "Save API Key"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
