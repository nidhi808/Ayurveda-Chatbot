import sys
import io
import wave

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
print("=============================================")
print("🌿 COMPREHENSIVE AYURBOT FEATURE TEST SUITE")
print("=============================================")

# 1. Health check
res = client.get("/api/health")
assert res.status_code == 200
data = res.json()
print(f"1. Health Check: OK (chunks={data['chunks_indexed']}, status={data['status']})")

# 2. Categories
res = client.get("/api/categories")
assert res.status_code == 200
cats = res.json()
print(f"2. Categories: OK ({len(cats)} categories: {cats})")

# 3. Sources Listing & Filtering
res = client.get("/api/sources")
assert res.status_code == 200
all_src = res.json()
res_herbs = client.get("/api/sources?category=Herbs")
herbs_src = res_herbs.json()
print(f"3. Sources Filter: OK (total={len(all_src)}, herbs={len(herbs_src)})")

# 4. English Chat Query & RAG Retrieval
res = client.post("/api/chat", json={"message": "What are the three doshas and their elements?", "language": "en"})
assert res.status_code == 200
chat1 = res.json()
conv_id = chat1["conversation_id"]
print(f"4. English Chat: OK (conv_id={conv_id[:8]}..., sources={len(chat1['sources'])}, top_source='{chat1['sources'][0]['title']}')")

# 5. Multi-turn Follow-up
res = client.post("/api/chat", json={"conversation_id": conv_id, "message": "How does diet affect them?", "language": "en"})
assert res.status_code == 200
chat2 = res.json()
assert chat2["conversation_id"] == conv_id
print("5. Multi-turn Follow-up: OK (persisted in same conversation)")

# 6. Conversation History Endpoint
res = client.get(f"/api/conversations/{conv_id}")
assert res.status_code == 200
hist = res.json()
print(f"6. Conversation History: OK ({len(hist['messages'])} messages stored)")

# 7. Marathi Chat Query (khokla sathi aushadh)
res = client.post("/api/chat", json={"message": "khokla sathi aushadh", "language": "mr"})
assert res.status_code == 200
mr_chat = res.json()
assert mr_chat["language"] == "mr"
assert any("Yashtimadhu" in s["title"] or "Tulsi" in s["title"] or "Sitopaladi" in s["title"] for s in mr_chat["sources"])
print(f"7. Marathi Chat: OK (sources={len(mr_chat['sources'])}, top_source='{mr_chat['sources'][0]['title']}', answer_lang={mr_chat['language']})")

# 8. Hindi Chat Query
res = client.post("/api/chat", json={"message": "दिनचर्या के क्या नियम हैं?", "language": "hi"})
assert res.status_code == 200
hi_chat = res.json()
assert hi_chat["language"] == "hi"
print(f"8. Hindi Chat: OK (sources={len(hi_chat['sources'])}, answer_lang={hi_chat['language']})")

# 9. Safety Guardrail: Emergency interception
res = client.post("/api/chat", json={"message": "I have severe chest pain and cannot breathe."})
assert res.status_code == 200
safe1 = res.json()
assert safe1["safety_triggered"] is True
print(f"9. Emergency Safety Guardrail: OK (triggered={safe1['safety_triggered']}, reason={safe1['safety_reason']})")

# 10. Safety Guardrail: Prescription/Dosage request interception
res = client.post("/api/chat", json={"message": "How many mg tablets of antibiotic should I take?"})
assert res.status_code == 200
safe2 = res.json()
assert safe2["safety_triggered"] is True
print(f"10. Prescription Safety Guardrail: OK (triggered={safe2['safety_triggered']}, reason={safe2['safety_reason']})")

# 11. User Feedback Submission
res = client.post("/api/feedback", json={"message_id": chat1["message_id"], "rating": 5, "feedback": "Great citation accuracy!"})
assert res.status_code == 200
print(f"11. Feedback Submission: OK (status={res.json()['status']})")

# 12. RAG Evaluation Benchmark
res = client.get("/api/evaluate?top_k=3")
assert res.status_code == 200
eval_res = res.json()
print(f"12. RAG Evaluation Suite: OK (grounded_score={eval_res['grounded_score']}%, precision_at_k={eval_res['precision_at_k']}%, safety_accuracy={eval_res['safety_detection_accuracy']}%, total_questions={eval_res['total_questions']})")

# 13. Whisper.cpp Speech-to-Text Transcription
buf = io.BytesIO()
with wave.open(buf, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(b"\x00\x00" * 16000)
res = client.post("/api/transcribe", files={"file": ("test.wav", buf.getvalue(), "audio/wav")}, data={"language": "auto"})
assert res.status_code == 200
trans = res.json()
print(f"13. Whisper.cpp Audio Transcribe: OK (engine={trans['engine']}, lang={trans['language']})")

print("=============================================")
print("🎉 ALL 13 CORE BACKEND FEATURES PASSED 100%")
print("=============================================")
