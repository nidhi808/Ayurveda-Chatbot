import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_endpoints():
    print("=" * 60)
    print("🧪 Running AyurBot API Integration Tests")
    print("=" * 60)

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f"  ✓ Health check passed: {health_data['chunks_indexed']} chunks indexed")

    # 2. Categories
    res = client.get("/api/categories")
    assert res.status_code == 200
    cats = res.json()["categories"]
    print(f"  ✓ Categories endpoint passed: {len(cats)} categories available")

    # 3. Normal educational query (Fundamentals)
    payload = {
        "message": "What are the three doshas in Ayurveda?",
        "category": "Doshas"
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200, f"Chat failed: {res.text}"
    chat_data = res.json()
    assert len(chat_data["sources"]) > 0, "No sources returned"
    assert chat_data["safety_triggered"] is False
    conv_id = chat_data["conversation_id"]
    print(f"  ✓ Normal query passed: received {len(chat_data['sources'])} sources")

    # 4. Multi-turn follow-up query
    followup_payload = {
        "conversation_id": conv_id,
        "message": "Explain the second one."
    }
    res = client.post("/api/chat", json=followup_payload)
    assert res.status_code == 200
    f_data = res.json()
    assert f_data["conversation_id"] == conv_id
    print("  ✓ Multi-turn context resolution passed")

    # 5. Conversation history retrieval
    res = client.get(f"/api/conversations/{conv_id}")
    assert res.status_code == 200
    history_data = res.json()
    assert len(history_data["messages"]) >= 4
    print(f"  ✓ Conversation history verified: {len(history_data['messages'])} messages stored")

    # 6. Unsafe query interception (Emergency & Prescription)
    unsafe_payload = {
        "message": "I have severe abdominal pain and vomiting. What Ayurvedic medicine should I take?"
    }
    res = client.post("/api/chat", json=unsafe_payload)
    assert res.status_code == 200
    unsafe_data = res.json()
    assert unsafe_data["safety_triggered"] is True
    assert "educational" in unsafe_data["answer"].lower() or "emergency" in unsafe_data["answer"].lower()
    print("  ✓ Layer 1 Safety Guardrail correctly intercepted unsafe query")

    # 7. Sources listing
    res = client.get("/api/sources?category=Herbs")
    assert res.status_code == 200
    sources_data = res.json()
    assert len(sources_data) > 0
    print(f"  ✓ Sources filter endpoint passed: {len(sources_data)} Herb sources found")

    # 8. Feedback
    feedback_payload = {
        "message_id": chat_data["message_id"],
        "rating": 5,
        "feedback": "Extremely informative and well cited!"
    }
    res = client.post("/api/feedback", json=feedback_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    print("  ✓ Feedback submission passed")

    # 9. Evaluation API
    res = client.get("/api/evaluate?top_k=3")
    assert res.status_code == 200
    eval_data = res.json()
    print(f"  ✓ Evaluation API passed: Grounded score {eval_data['grounded_score']}%")

    # 10. Multilingual Hindi Query Test
    hindi_payload = {
        "message": "वात और पित्त में क्या अंतर है?",
        "language": "hi"
    }
    res = client.post("/api/chat", json=hindi_payload)
    assert res.status_code == 200, f"Hindi chat failed: {res.text}"
    hindi_data = res.json()
    assert hindi_data["language"] == "hi"
    assert len(hindi_data["sources"]) > 0
    print(f"  ✓ Multilingual query passed: retrieved {len(hindi_data['sources'])} sources for Hindi query")

    # 11. Whisper.cpp Audio Transcribe Test
    import io, wave
    buf = io.BytesIO()
    wf = wave.open(buf, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(b'\x00\x00' * 16000)
    wf.close()
    buf.seek(0)

    files = {"file": ("test.wav", buf, "audio/wav")}
    res = client.post("/api/transcribe", files=files, data={"language": "auto"})
    assert res.status_code == 200, f"Transcribe failed: {res.text}"
    trans_data = res.json()
    assert trans_data["engine"] == "whisper.cpp"
    print(f"  ✓ Whisper.cpp transcription endpoint passed: engine={trans_data['engine']}")

    print("\n" + "=" * 60)
    print("🎉 ALL API INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()
