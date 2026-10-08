"""
Test suite for Ayurvedic Clinical Consultation (Rogi Pariksha & Prashna Pariksha Workflow).
Verifies:
1. Symptom detection across categories (cough, digestion, joint pain, stress/sleep, skin)
2. Clarifying intake questions (duration, age, gender, medical history, symptom-specific)
3. Personalized Ayurvedic protocol with herbs, When & How to take (Sewan Vidhi & Anupana), and Pathya/Apathya
4. Multilingual support (English, Hindi, Marathi)
5. Botanical image delivery for symptom categories
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

from fastapi.testclient import TestClient
from backend.app.main import app

def test_consultation_flow():
    client = TestClient(app)
    print("=" * 60)
    print("🌿 AYURBOT CLINICAL CONSULTATION (ROGI PARIKSHA) TEST SUITE")
    print("=" * 60)

    # ---------------------------------------------------------
    # Test 1: English Cough Intake -> Clarifying Questions
    # ---------------------------------------------------------
    print("1. Testing English Cough Intake Questioning...")
    r1 = client.post("/api/chat", json={"message": "I have a terrible cough and cold"})
    assert r1.status_code == 200, f"Status code error: {r1.status_code}"
    d1 = r1.json()
    assert "Rogi Pariksha" in d1["answer"] or "Patient Intake" in d1["answer"], "Did not initiate Rogi Pariksha intake"
    assert "Duration" in d1["answer"], "Missing Duration question"
    assert "Age & Gender" in d1["answer"], "Missing Age & Gender question"
    assert "Medical History" in d1["answer"], "Missing Medical History question"
    assert "dry (Vataja)" in d1["answer"] or "cough" in d1["answer"].lower(), "Missing cough-specific question"
    assert d1.get("image") is not None, "Missing herb image in consultation response"
    assert "tulsi" in d1["image"]["url"].lower(), f"Expected Tulsi image for cough, got {d1['image']['url']}"
    conv_id = d1["conversation_id"]
    print("   ✅ PASS: Asked 4 clarifying questions + attached Tulsi botanical image card")

    # ---------------------------------------------------------
    # Test 2: Multi-turn Protocol Delivery with Sewan Vidhi
    # ---------------------------------------------------------
    print("2. Testing Multi-turn Protocol Delivery with Sewan Vidhi & Timing...")
    r2 = client.post("/api/chat", json={
        "conversation_id": conv_id,
        "message": "Age 28, Male, 3 days, dry cough, no other illness"
    })
    assert r2.status_code == 200, f"Status code error: {r2.status_code}"
    d2 = r2.json()
    ans2 = d2["answer"]
    assert "Personalized Ayurvedic" in ans2 or "Guidance Protocol" in ans2 or "Customized Protocol" in ans2, "Missing protocol heading"
    assert "Sitopaladi" in ans2, "Expected Sitopaladi formulation in cough protocol"
    assert "When and How to Take" in ans2 or "Sewan Vidhi" in ans2 or "Morning" in ans2, "Missing When and How to take section"
    assert "Anupana" in ans2 or "Honey" in ans2, "Missing Anupana / carrier"
    assert "Pathya" in ans2 and "Apathya" in ans2, "Missing Pathya / Apathya dietary guidelines"
    print("   ✅ PASS: Generated tailored protocol with herbs, morning/night timing, Anupana, and Pathya/Apathya")

    # ---------------------------------------------------------
    # Test 3: Hindi Acidity / Digestive Consultation
    # ---------------------------------------------------------
    print("3. Testing Hindi Acidity / Digestive Consultation...")
    r3 = client.post("/api/chat", json={"message": "mujhe 4 din se pet me gas aur acidity ho rahi hai"})
    assert r3.status_code == 200
    d3 = r3.json()
    ans3 = d3["answer"]
    assert "रोगी परीक्षा" in ans3 or "Rogi Pariksha" in ans3, "Missing Hindi Rogi Pariksha"
    assert "अवधि" in ans3 or "Duration" in ans3, "Missing Hindi duration question"
    assert "आयु एवं लिंग" in ans3 or "उम्र" in ans3, "Missing Hindi age question"
    assert d3.get("image") is not None, "Missing herb image for digestive symptom"
    assert "triphala" in d3["image"]["url"].lower(), f"Expected Triphala image, got {d3['image']['url']}"
    print("   ✅ PASS: Hindi digestive intake questions asked + Triphala image card")

    # ---------------------------------------------------------
    # Test 4: Hindi Multi-turn Intake Response -> Protocol
    # ---------------------------------------------------------
    print("4. Testing Hindi Protocol Synthesis...")
    r4 = client.post("/api/chat", json={
        "conversation_id": d3["conversation_id"],
        "message": "उम्र 35, पुरुष, 4 दिन से, सीने में जलन और खट्टी डकार, कोई अन्य बीमारी नहीं"
    })
    assert r4.status_code == 200
    d4 = r4.json()
    ans4 = d4["answer"]
    assert "आयुर्वेदिक" in ans4 and "सेवन विधि" in ans4, "Missing Hindi Sewan Vidhi section"
    assert "त्रिफला" in ans4 or "Triphala" in ans4, "Expected Triphala in digestive protocol"
    assert "पथ्य" in ans4 and "अपथ्य" in ans4, "Missing Hindi Pathya & Apathya"
    print("   ✅ PASS: Hindi tailored protocol with Sewan Vidhi, Anupana, Pathya/Apathya generated")

    # ---------------------------------------------------------
    # Test 5: Marathi Joint Pain Consultation
    # ---------------------------------------------------------
    print("5. Testing Marathi Joint Pain Consultation...")
    r5 = client.post("/api/chat", json={"message": "माझ्या गुडघ्यात खूप वेदना आणि कडकपणा आहे"})
    assert r5.status_code == 200
    d5 = r5.json()
    ans5 = d5["answer"]
    assert "रोगी परीक्षा" in ans5 or "Rogi Pariksha" in ans5, "Missing Marathi Rogi Pariksha"
    assert d5.get("image") is not None, "Missing herb image for joint pain"
    assert "ashwagandha" in d5["image"]["url"].lower(), f"Expected Ashwagandha image, got {d5['image']['url']}"
    print("   ✅ PASS: Marathi joint pain intake + Ashwagandha botanical image card")

    # ---------------------------------------------------------
    # Test 6: Single-prompt complete details (Bypasses questions directly to protocol)
    # ---------------------------------------------------------
    print("6. Testing Single-Prompt with Full Intake Details...")
    r6 = client.post("/api/chat", json={
        "message": "I am a 30 year old male, having dry cough for 5 days, no other illness"
    })
    assert r6.status_code == 200
    d6 = r6.json()
    ans6 = d6["answer"]
    assert "Personalized Ayurvedic" in ans6 or "Guidance Protocol" in ans6, "Expected immediate protocol for complete prompt"
    assert "When and How to Take" in ans6 or "Sewan Vidhi" in ans6, "Expected Sewan Vidhi in single-turn protocol"
    print("   ✅ PASS: Single prompt with full details directly synthesizes tailored protocol")

    print("=" * 60)
    print("🎉 ALL 6 AYURVEDIC CONSULTATION TESTS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_consultation_flow()
