import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import SourceViewer from "./components/SourceViewer";
import KnowledgeExplorer from "./components/KnowledgeExplorer";
import EvaluationModal from "./components/EvaluationModal";
import SettingsModal from "./components/SettingsModal";
import { checkHealth, fetchCategories, sendChatMessage } from "./api";

const STORAGE_KEY = "ayurbot_conversations";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [categories, setCategories] = useState([{ name: "All", count: 28 }]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedLanguage, setSelectedLanguage] = useState("auto");

  const [conversations, setConversations] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);

  // Modals state
  const [activeSource, setActiveSource] = useState(null);
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [evaluationOpen, setEvaluationOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Load health and categories on mount
  useEffect(() => {
    async function init() {
      const health = await checkHealth();
      setHealthStatus(health);

      const catData = await fetchCategories();
      if (catData && catData.categories) {
        setCategories(catData.categories);
      }
    }
    init();
  }, []);

  // Save conversations to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch (err) {
      console.warn("Failed to persist conversations:", err);
    }
  }, [conversations]);

  // When active conversation changes, load its messages
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }
    const current = conversations.find((c) => c.id === activeConversationId);
    if (current) {
      setMessages(current.messages || []);
    }
  }, [activeConversationId]);

  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInputText("");
  };

  const handleDeleteConversation = (id) => {
    const updated = conversations.filter((c) => c.id !== id);
    setConversations(updated);
    if (activeConversationId === id) {
      setActiveConversationId(null);
      setMessages([]);
    }
  };

  const handleSendMessage = async (queryText) => {
    const text = queryText || inputText;
    if (!text.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputText("");
    setLoading(true);

    try {
      const response = await sendChatMessage({
        conversation_id: activeConversationId,
        message: text,
        category: selectedCategory,
        language: selectedLanguage
      });

      const botMessage = {
        id: response.message_id,
        role: "assistant",
        content: response.answer,
        sources: response.sources || [],
        category: response.category,
        language: response.language,
        safety_triggered: response.safety_triggered,
        safety_reason: response.safety_reason,
        suggested_followups: response.suggested_followups || [],
        timestamp: new Date().toLocaleTimeString()
      };

      const updatedMessages = [...newMessages, botMessage];
      setMessages(updatedMessages);

      const convId = response.conversation_id;
      setActiveConversationId(convId);

      // Update or insert conversation in sidebar
      setConversations((prev) => {
        const existingIdx = prev.findIndex((c) => c.id === convId);
        const titleSnippet = text.length > 32 ? text.slice(0, 32) + "..." : text;
        if (existingIdx >= 0) {
          const clone = [...prev];
          clone[existingIdx] = {
            ...clone[existingIdx],
            messages: updatedMessages
          };
          return clone;
        } else {
          return [
            {
              id: convId,
              title: titleSnippet,
              created_at: new Date().toISOString(),
              messages: updatedMessages
            },
            ...prev
          ];
        }
      });
    } catch (err) {
      const errorMessage = {
        role: "assistant",
        content: `⚠️ Error contacting knowledge assistant: ${err.message}. Please make sure the FastAPI backend is running.`,
        sources: [],
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPrompt = (promptQuestion, promptCategory) => {
    if (promptCategory) {
      setSelectedCategory(promptCategory);
    }
    handleSendMessage(promptQuestion);
  };

  return (
    <div className="app-container">
      <Sidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={(id) => setActiveConversationId(id)}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        chunkCount={healthStatus?.chunks_indexed || 28}
      />

      <div className="main-wrapper">
        <Header
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          categories={categories}
          selectedCategory={selectedCategory}
          onSelectCategory={(cat) => setSelectedCategory(cat)}
          selectedLanguage={selectedLanguage}
          onSelectLanguage={(lang) => setSelectedLanguage(lang)}
          onOpenExplorer={() => setExplorerOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenEvaluation={() => setEvaluationOpen(true)}
          healthStatus={healthStatus}
        />

        <ChatWindow
          messages={messages}
          inputText={inputText}
          setInputText={setInputText}
          onSendMessage={handleSendMessage}
          loading={loading}
          selectedCategory={selectedCategory}
          selectedLanguage={selectedLanguage}
          onSelectPrompt={handleSelectPrompt}
          onSelectSource={(source) => setActiveSource(source)}
        />
      </div>

      {/* Modals & Overlays */}
      {activeSource && (
        <SourceViewer
          source={activeSource}
          onClose={() => setActiveSource(null)}
        />
      )}

      {explorerOpen && (
        <KnowledgeExplorer
          onClose={() => setExplorerOpen(false)}
          onSelectTopic={(title, category) => {
            if (category) setSelectedCategory(category);
            handleSendMessage(`Tell me about ${title}`);
          }}
        />
      )}

      {evaluationOpen && (
        <EvaluationModal onClose={() => setEvaluationOpen(false)} />
      )}

      {settingsOpen && (
        <SettingsModal
          onClose={() => setSettingsOpen(false)}
          currentModel={healthStatus?.model}
        />
      )}
    </div>
  );
}
