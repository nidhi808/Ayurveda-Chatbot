import React, { useRef, useEffect, useState } from "react";
import { Send, Sparkles, Compass, Leaf, Sun, Flame, BookMarked, Mic, MicOff, Loader2 } from "lucide-react";
import ChatMessage from "./ChatMessage";
import { uploadAndTranscribeAudio } from "../api";

const STARTER_PROMPTS = [
  {
    category: "Doshas",
    icon: Compass,
    question: "What are the three doshas and how do they balance the body?",
    tag: "Tridosha"
  },
  {
    category: "Fundamentals",
    icon: Flame,
    question: "What is the difference between Prakriti and Vikriti?",
    tag: "Constitution"
  },
  {
    category: "Lifestyle",
    icon: Sun,
    question: "What is Dinacharya and what are its essential morning steps?",
    tag: "Daily Routine"
  },
  {
    category: "Herbs",
    icon: Leaf,
    question: "What are the traditional qualities and scientific evidence for Ashwagandha?",
    tag: "Rejuvenation"
  },
  {
    category: "Herbs",
    icon: Leaf,
    question: "What is Triphala and what three fruits make it up?",
    tag: "Formulations"
  },
  {
    category: "Traditional Concepts",
    icon: BookMarked,
    question: "What is the Brihat Trayi in classical Ayurvedic literature?",
    tag: "Classics"
  }
];

export default function ChatWindow({
  messages,
  inputText,
  setInputText,
  onSendMessage,
  loading,
  selectedCategory,
  selectedLanguage,
  onSelectPrompt,
  onSelectSource
}) {
  const messagesEndRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // -------------------------------------------------------------
  // Voice Input using whisper.cpp + Web Audio / MediaRecorder
  // -------------------------------------------------------------
  const toggleRecording = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });

        if (audioBlob.size > 500) {
          setTranscribing(true);
          try {
            const data = await uploadAndTranscribeAudio(audioBlob, selectedLanguage);
            if (data && data.text && data.text.trim()) {
              setInputText(data.text.trim());
            }
          } catch (err) {
            console.warn("[Voice] whisper.cpp local transcription error:", err);
          } finally {
            setTranscribing(false);
          }
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access could not be granted. Please check browser permissions.");
    }
  };

  return (
    <div className="main-wrapper">
      <div className="chat-scroll-container">
        <div className="chat-content-width">
          {messages.length === 0 ? (
            <div className="welcome-hero">
              <div className="welcome-lotus">🌿</div>
              <h2 className="welcome-title">AyurBot Knowledge Assistant</h2>
              <p className="welcome-subtitle">
                Explore source-grounded Ayurvedic wisdom, classical principles, and herb monographs.
                Every response is cited directly from authentic AYUSH & classical repositories.
              </p>

              <div className="welcome-grid">
                {STARTER_PROMPTS.map((item, idx) => {
                  const IconComp = item.icon;
                  return (
                    <div
                      key={idx}
                      className="prompt-card"
                      onClick={() => onSelectPrompt(item.question, item.category)}
                    >
                      <div className="prompt-category">
                        <IconComp size={12} />
                        <span>{item.category} • {item.tag}</span>
                      </div>
                      <div className="prompt-question">{item.question}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <ChatMessage
                key={index}
                message={msg}
                onSelectSource={onSelectSource}
                onSelectFollowup={(q) => onSendMessage(q)}
              />
            ))
          )}

          {loading && (
            <div className="message-row bot">
              <div className="bot-card" style={{ padding: "16px 20px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#2d6a4f", fontSize: "14px" }}>
                  <Sparkles size={16} className="animate-spin" />
                  <span>Retrieving Ayurvedic sources & synthesizing grounded answer...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Input Dock */}
      <div className="input-dock">
        <form className="input-box-wrapper" onSubmit={handleSubmit}>
          {selectedCategory && selectedCategory !== "All" && (
            <span
              style={{
                fontSize: "12px",
                background: "#e8efe9",
                color: "#214a37",
                padding: "3px 8px",
                borderRadius: "12px",
                fontWeight: "600",
                whiteSpace: "nowrap"
              }}
            >
              {selectedCategory}
            </span>
          )}

          <input
            type="text"
            className="chat-input"
            placeholder={
              transcribing
                ? "🎙️ Transcribing audio with local whisper.cpp (offline)..."
                : selectedLanguage === "mr"
                ? "आयुर्वेद, खोकला, वात-पित्त-कफ, दिनचर्या, किंवा औषधी वनस्पतींबद्दल विचारा..."
                : selectedLanguage === "hi"
                ? "आयुर्वेद, वात-पित्त-कफ, दिनचर्या, या जड़ी-बूटियों के बारे में पूछें..."
                : selectedLanguage === "sa"
                ? "आयुर्वेदस्य मूलसिद्धान्तान् पृच्छतु..."
                : selectedCategory && selectedCategory !== "All"
                ? `Ask about ${selectedCategory} (e.g., characteristics, concepts, classical uses)...`
                : "Ask about doshas, herbs, daily routine, or Ayurvedic concepts..."
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          {/* Whisper.cpp Microphone Button */}
          <button
            type="button"
            className={`icon-btn ${isRecording ? "active" : ""}`}
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              backgroundColor: isRecording ? "#fde8e8" : "transparent",
              color: isRecording ? "#d94826" : "#607469"
            }}
            onClick={toggleRecording}
            title={isRecording ? "Stop recording (whisper.cpp)" : "Speak via whisper.cpp"}
          >
            {transcribing ? (
              <Loader2 size={18} className="animate-spin" color="#2d6a4f" />
            ) : isRecording ? (
              <MicOff size={18} color="#d94826" />
            ) : (
              <Mic size={18} />
            )}
          </button>

          <button
            type="submit"
            className="btn-send"
            disabled={!inputText.trim() || loading}
            title="Send query"
          >
            <Send size={18} />
          </button>
        </form>

        <div className="input-legal-notice">
          🌿 AyurBot is an educational assistant with whisper.cpp voice input. Consult healthcare professionals for medical advice.
        </div>
      </div>
    </div>
  );
}
