import React, { useState } from "react";
import { X, Play, CheckCircle2, XCircle, Award, ShieldCheck, Target, RefreshCw } from "lucide-react";
import { runEvaluation } from "../api";

export default function EvaluationModal({ onClose }) {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRunEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runEvaluation();
      setEvalData(data);
    } catch (err) {
      setError(err.message || "Failed to run evaluation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "780px" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: "#fdf3e2",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#c9933b"
              }}
            >
              <Award size={20} />
            </div>
            <div>
              <h3 className="modal-title">RAG Evaluation Benchmark</h3>
              <div style={{ fontSize: "12px", color: "#6d8276" }}>
                Quantitative assessment of retrieval precision, safety guardrails & grounding
              </div>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-content" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div
            style={{
              background: "#f4f8f5",
              border: "1px solid #dbe6de",
              borderRadius: "12px",
              padding: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between"
            }}
          >
            <div>
              <div style={{ fontSize: "14px", fontWeight: "700", color: "#143828" }}>
                19 Benchmark Test Questions
              </div>
              <div style={{ fontSize: "12px", color: "#5d7367" }}>
                Covers Fundamentals, Doshas, Lifestyle, Herbs, Traditional Concepts, and Medical Safety.
              </div>
            </div>

            <button
              className="btn-new-chat"
              style={{ margin: 0, padding: "10px 18px", fontSize: "13px" }}
              onClick={handleRunEvaluation}
              disabled={loading}
            >
              {loading ? (
                <>
                  <RefreshCw size={15} className="animate-spin" />
                  <span>Evaluating...</span>
                </>
              ) : (
                <>
                  <Play size={15} />
                  <span>Run Benchmark</span>
                </>
              )}
            </button>
          </div>

          {error && (
            <div style={{ padding: "12px", background: "#fde8e8", color: "#9b1c1c", borderRadius: "8px", fontSize: "13px" }}>
              {error}
            </div>
          )}

          {evalData && (
            <>
              {/* Metric Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e1ebe3",
                    borderRadius: "12px",
                    padding: "16px",
                    textAlign: "center"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "center", marginBottom: "6px" }}>
                    <Target size={20} color="#2d6a4f" />
                  </div>
                  <div style={{ fontSize: "24px", fontWeight: "800", color: "#143828" }}>
                    {evalData.precision_at_k}%
                  </div>
                  <div style={{ fontSize: "12px", fontWeight: "600", color: "#5d7367" }}>
                    Precision@3
                  </div>
                </div>

                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e1ebe3",
                    borderRadius: "12px",
                    padding: "16px",
                    textAlign: "center"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "center", marginBottom: "6px" }}>
                    <ShieldCheck size={20} color="#2b9348" />
                  </div>
                  <div style={{ fontSize: "24px", fontWeight: "800", color: "#2b9348" }}>
                    {evalData.safety_detection_accuracy}%
                  </div>
                  <div style={{ fontSize: "12px", fontWeight: "600", color: "#5d7367" }}>
                    Safety Accuracy
                  </div>
                </div>

                <div
                  style={{
                    background: "#ffffff",
                    border: "1px solid #e1ebe3",
                    borderRadius: "12px",
                    padding: "16px",
                    textAlign: "center"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "center", marginBottom: "6px" }}>
                    <Award size={20} color="#c9933b" />
                  </div>
                  <div style={{ fontSize: "24px", fontWeight: "800", color: "#c9933b" }}>
                    {evalData.grounded_score}%
                  </div>
                  <div style={{ fontSize: "12px", fontWeight: "600", color: "#5d7367" }}>
                    Overall Grounded
                  </div>
                </div>
              </div>

              {/* Itemized list */}
              <div>
                <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#143828", marginBottom: "10px" }}>
                  Itemized Test Results ({evalData.details.length})
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "280px", overflowY: "auto" }}>
                  {evalData.details.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        background: item.passed ? "#f7faf7" : "#fff8f8",
                        border: `1px solid ${item.passed ? "#d2e4d6" : "#fcd8d8"}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        fontSize: "13px"
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                        {item.passed ? (
                          <CheckCircle2 size={16} color="#2b9348" style={{ flexShrink: 0 }} />
                        ) : (
                          <XCircle size={16} color="#d94826" style={{ flexShrink: 0 }} />
                        )}
                        <span style={{ fontWeight: "600", color: "#32443c", whiteSpace: "nowrap" }}>
                          [{item.category}]
                        </span>
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#4d6056" }}>
                          {item.question}
                        </span>
                      </div>

                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: "700",
                          padding: "2px 8px",
                          borderRadius: "12px",
                          background: item.passed ? "#d8eedc" : "#fde2e2",
                          color: item.passed ? "#1b632e" : "#b02a2a",
                          flexShrink: 0
                        }}
                      >
                        {item.passed ? "PASSED" : "FAILED"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
