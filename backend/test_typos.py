import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

test_queries = [
    ("tell me about triphla", "en", "triphala"),
    ("what is prakruti", "en", "prakriti"),
    ("ashwgandha benefits", "en", "ashwagandha"),
    ("triphla ke fyde", "hi", "triphala"),
    ("prakruti kya hoti hai", "hi", "prakriti"),
    ("auredik tips for healthy life", "en", "ayurveda"),
    ("rtucharya rules", "en", "ritucharya"),
    ("virudha ahar kya hai", "hi", "viruddha"),
    ("aswagandha and tulsee ke aushadhi gun", "hi", "ashwagandha"),
    ("kuff aur khasi ke auredik upay", "hi", "kapha"),
    ("khoklya sathi tulas", "mr", "tulsi"),
    ("dincharya ke niyam", "hi", "dinacharya"),
    ("kuf dosh symptoms", "en", "kapha"),
    ("aurvedik remedies for jukham and bukhar", "hi", "fever"),
    ("sar dard aur stress ke liye brahmi", "hi", "brahmi")
]

print("====================================================")
print("🌿 AYURBOT TYPO & SPELL CORRECTION TEST SUITE")
print("====================================================")

all_passed = True
for idx, (q, lang, tag) in enumerate(test_queries, 1):
    res = client.post("/api/chat", json={"message": q, "language": lang})
    assert res.status_code == 200
    data = res.json()
    src_count = len(data["sources"])
    interp = data.get("interpreted_query")
    answer = data.get("answer", "")

    no_data_phrase = (
        "couldn't find" in answer.lower()
        or "पुरेशी माहिती मिळाली नाही" in answer
        or "पर्याप्त जानकारी नहीं मिली" in answer
    )

    passed = (src_count > 0) and (not no_data_phrase)
    if not passed:
        all_passed = False

    status = "✅ PASS" if passed else "❌ FAIL"
    top_src = data["sources"][0]["title"] if src_count > 0 else "NONE"
    print(f"{idx}. {status} Query: '{q}' [{lang}]")
    print(f"   Understood: {interp or 'Direct match'}")
    print(f"   Sources: {src_count} | Top: {top_src}")
    print("-" * 52)

print(f"OVERALL RESULT: {'🎉 ALL TESTS PASSED 100%' if all_passed else '❌ SOME TESTS FAILED'}")
assert all_passed, "Not all typo tests passed!"
