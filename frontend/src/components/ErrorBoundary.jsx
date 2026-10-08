import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[AyurBot ErrorBoundary] Caught error:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
            background: "#f7faf7",
            padding: "24px",
            fontFamily: "Inter, sans-serif"
          }}
        >
          <div
            style={{
              maxWidth: "480px",
              background: "#ffffff",
              borderRadius: "16px",
              padding: "32px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
              border: "1px solid #dce8df",
              textAlign: "center"
            }}
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                background: "#fde8e8",
                color: "#c83232",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 16px"
              }}
            >
              <AlertCircle size={28} />
            </div>
            <h2 style={{ fontSize: "20px", color: "#143828", marginBottom: "8px" }}>
              Something went wrong
            </h2>
            <p style={{ fontSize: "14px", color: "#5a7064", lineHeight: "1.6", marginBottom: "24px" }}>
              AyurBot encountered an unexpected rendering error. Your chat history in localStorage is preserved.
            </p>
            <button
              onClick={this.handleReload}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                background: "#2d6a4f",
                color: "#ffffff",
                border: "none",
                borderRadius: "10px",
                padding: "10px 20px",
                fontSize: "14px",
                fontWeight: "600",
                cursor: "pointer"
              }}
            >
              <RotateCcw size={16} />
              Reload AyurBot
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
