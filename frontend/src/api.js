const API_BASE = "http://127.0.0.1:8000/api";

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    console.warn("Backend health check failed:", err);
    return null;
  }
}

export async function fetchCategories() {
  try {
    const res = await fetch(`${API_BASE}/categories`);
    if (!res.ok) throw new Error("Failed to load categories");
    return await res.json();
  } catch (err) {
    console.error("Error fetching categories:", err);
    return { categories: [{ name: "All", count: 28 }] };
  }
}

export async function sendChatMessage({ conversation_id, message, category, language }) {
  const payload = {
    conversation_id: conversation_id || null,
    message,
    category: category && category !== "All" ? category : null,
    language: language || "auto"
  };

  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${res.status})`);
  }

  return await res.json();
}

export async function fetchSources(category = null, skip = 0, limit = 100) {
  try {
    const params = new URLSearchParams();
    if (category && category !== "All") params.append("category", category);
    if (skip > 0) params.append("skip", String(skip));
    if (limit) params.append("limit", String(limit));
    const qs = params.toString();
    const url = qs ? `${API_BASE}/sources?${qs}` : `${API_BASE}/sources`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch sources");
    return await res.json();
  } catch (err) {
    console.error("Error fetching sources:", err);
    return [];
  }
}

export async function fetchConversationHistory(conversationId) {
  try {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}`);
    if (!res.ok) throw new Error("Failed to fetch history");
    return await res.json();
  } catch (err) {
    console.error("Error fetching history:", err);
    return null;
  }
}

export async function submitFeedback({ message_id, rating, feedback = "" }) {
  try {
    const res = await fetch(`${API_BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id, rating, feedback })
    });
    return await res.json();
  } catch (err) {
    console.error("Error submitting feedback:", err);
    return { status: "error" };
  }
}

export async function runEvaluation() {
  const res = await fetch(`${API_BASE}/evaluate?top_k=3`);
  if (!res.ok) throw new Error("Evaluation failed");
  return await res.json();
}

export async function uploadAndTranscribeAudio(audioBlob, language = "auto") {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.wav");
  formData.append("language", language);

  const res = await fetch(`${API_BASE}/transcribe`, {
    method: "POST",
    body: formData
  });

  if (!res.ok) {
    throw new Error(`Audio transcription failed (${res.status})`);
  }

  return await res.json();
}

export async function configureGeminiKey(apiKey) {
  const res = await fetch(`${API_BASE}/config/gemini-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey })
  });
  if (!res.ok) throw new Error("Failed to update key");
  return await res.json();
}
