import React, { useRef, useEffect, useState } from "react";
import { Send, Sparkles, Compass, Leaf, Sun, Flame, BookMarked, Mic, MicOff, Loader2 } from "lucide-react";
import ChatMessage from "./ChatMessage";
import { uploadAndTranscribeAudio } from "../api";
import { convertBlobTo16kHzWav } from "../utils/audioUtils";

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
  onSelectCategory,
  selectedLanguage,
  onSelectPrompt,
  onSelectSource
}) {
  const messagesEndRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const liveTranscriptRef = useRef("");

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, []);

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
  // Voice Input: Resilient Dual-Engine (Web Speech API + Backend Gemini/Whisper)
  // -------------------------------------------------------------
  const stopRecordingSession = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }
    setIsRecording(false);
  };

  const toggleRecording = async () => {
    if (isRecording) {
      stopRecordingSession();
      return;
    }

    liveTranscriptRef.current = "";
    setRecordingSeconds(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      let mimeType = "";
      if (typeof MediaRecorder !== "undefined") {
        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/webm")) {
          mimeType = "audio/webm";
        } else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) {
          mimeType = "audio/ogg;codecs=opus";
        }
      }

      const mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const rawBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" });

        // If Web Speech API already transcribed the speech live, keep it
        if (liveTranscriptRef.current && liveTranscriptRef.current.trim().length > 0) {
          return;
        }

        // Otherwise, send recorded audio to Gemini / Whisper backend
        if (rawBlob.size > 800) {
          setTranscribing(true);
          try {
            const pcmWavBlob = await convertBlobTo16kHzWav(rawBlob);
            const data = await uploadAndTranscribeAudio(pcmWavBlob, selectedLanguage);
            if (data && data.text && data.text.trim()) {
              setInputText((prev) => {
                const trimmed = data.text.trim();
                return prev && !prev.includes(trimmed) ? `${prev} ${trimmed}`.trim() : trimmed;
              });
            } else if (data && data.error) {
              console.warn("[Voice] Backend notice:", data.error);
            } else {
              alert("No clear speech detected. Please speak closer to your microphone or type your question.");
            }
          } catch (err) {
            console.error("[Voice] Backend transcription error:", err);
            alert("Voice transcription could not be completed. You can type your question in the text box.");
          } finally {
            setTranscribing(false);
          }
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);

      // Auto-stop after 20 seconds maximum
      let elapsed = 0;
      recordingTimerRef.current = setInterval(() => {
        elapsed += 1;
        setRecordingSeconds(elapsed);
        if (elapsed >= 20) {
          stopRecordingSession();
        }
      }, 1000);

      // Concurrently run Web Speech Recognition if supported for live typing preview
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognitionRef.current = recognition;
          recognition.continuous = true;
          recognition.interimResults = true;

          if (selectedLanguage === "mr") {
            recognition.lang = "mr-IN";
          } else if (selectedLanguage === "hi") {
            recognition.lang = "hi-IN";
          } else {
            recognition.lang = "en-IN";
          }

          recognition.onresult = (event) => {
            let transcript = "";
            for (let i = 0; i < event.results.length; i++) {
              transcript += event.results[i][0].transcript;
            }
            if (transcript.trim()) {
              liveTranscriptRef.current = transcript.trim();
              setInputText(transcript.trim());
            }
          };

          recognition.onerror = (event) => {
            console.warn("[Voice] Web Speech API notice (audio will still be transcribed by Gemini backend):", event.error);
          };

          recognition.onend = () => {};
          recognition.start();
        } catch (err) {
          console.warn("[Voice] Web Speech API start notice:", err);
        }
      }
    } catch (err) {
      console.error("[Voice] Microphone access error:", err);
      setIsRecording(false);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        alert("Microphone permission was denied. Please click the lock or settings icon in your browser address bar and enable Microphone access.");
      } else {
        alert("Could not access microphone. Please ensure your microphone is connected.");
      }
    }
  };

  return (
    <div className="chat-window">
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
                onSelectFollowup={(q) => onSendMessage(q, "All")}
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
        {(isRecording || transcribing) && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              background: isRecording ? "#fef2f2" : "#f0fdf4",
              border: `1px solid ${isRecording ? "#fca5a5" : "#86efac"}`,
              borderRadius: "12px",
              padding: "8px 16px",
              marginBottom: "10px",
              fontSize: "13px",
              color: isRecording ? "#991b1b" : "#166534",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)"
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: "600" }}>
              {isRecording ? (
                <>
                  <span
                    style={{
                      display: "inline-block",
                      width: "10px",
                      height: "10px",
                      borderRadius: "50%",
                      background: "#ef4444"
                    }}
                  />
                  <span>Listening... Speak your question now</span>
                  <span style={{ opacity: 0.75, fontWeight: "500", fontSize: "12px" }}>
                    ({recordingSeconds}s / 20s)
                  </span>
                </>
              ) : (
                <>
                  <Loader2 size={16} className="animate-spin" color="#166534" />
                  <span>Transcribing speech with AI...</span>
                </>
              )}
            </div>
            {isRecording && (
              <button
                type="button"
                onClick={stopRecordingSession}
                style={{
                  background: "#ef4444",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  padding: "4px 12px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer"
                }}
              >
                Done Speaking
              </button>
            )}
          </div>
        )}

        <form className="input-box-wrapper" onSubmit={handleSubmit}>
          {selectedCategory && selectedCategory !== "All" && (
            <span
              onClick={() => onSelectCategory && onSelectCategory("All")}
              title="Click to remove category filter (search across all Ayurvedic categories)"
              style={{
                fontSize: "12px",
                background: "#e8efe9",
                color: "#214a37",
                padding: "3px 8px",
                borderRadius: "12px",
                fontWeight: "600",
                whiteSpace: "nowrap",
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                cursor: "pointer",
                transition: "all 0.15s ease"
              }}
            >
              <span>{selectedCategory}</span>
              <span style={{ fontSize: "11px", fontWeight: "bold", opacity: 0.7 }}>✕</span>
            </span>
          )}

          <input
            type="text"
            className="chat-input"
            placeholder={
              transcribing
                ? "🎙️ Transcribing audio with AI..."
                : isRecording
                ? "🔴 Listening to your voice... Speak clearly"
                : selectedLanguage === "mr"
                ? "आयुर्वेद, खोकला, वात-पित्त-कफ, किंवा औषधी वनस्पतींबद्दल विचारा..."
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

          {/* Voice Input Button */}
          <button
            type="button"
            className={`icon-btn ${isRecording ? "active" : ""}`}
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              backgroundColor: isRecording ? "#fde8e8" : "transparent",
              color: isRecording ? "#d94826" : "#607469",
              opacity: loading ? 0.5 : 1
            }}
            onClick={toggleRecording}
            disabled={loading}
            title={isRecording ? "Stop recording (click when done speaking)" : "Speak your Ayurvedic question"}
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
          🌿 AyurBot is an educational assistant with AI voice input. Consult healthcare professionals for medical advice.
        </div>
      </div>
    </div>
  );
}
