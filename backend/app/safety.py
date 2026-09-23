import re
from typing import Tuple, Optional

# Medical emergency & severe acute symptoms patterns
EMERGENCY_KEYWORDS = [
    r"\b(?:severe|acute|intense)\s+(?:abdominal\s+)?pain\b",
    r"\bchest\s+pain\b",
    r"\bheart\s+attack\b",
    r"\bstroke\b",
    r"\bseizure\b",
    r"\bsevere\s+bleeding\b",
    r"\bsuicide\b",
    r"\bpoisoning\b",
    r"\bunconscious\b",
    r"\bdifficulty\s+breathing\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bvomiting\b",
    r"\banaphylaxis\b",
    r"\bfever\s+of\s+10\d",
    # Hindi / Hinglish Emergency terms
    r"\b(?:tez|bahut|asahaaniya)\s+(?:dard|peeda)\b",
    r"\bchhati\s+me\s+dard\b",
    r"\bsaans\s+lene\s+me\s+takleef\b"
]

# Prescription / Dosage request patterns (English, Hindi, Hinglish)
PRESCRIPTION_KEYWORDS = [
    r"\bwhich\s+(?:\w+\s+)*(?:medicine|pill|drug|antibiotic|cure)\s+should\s+i\s+take\b",
    r"\bwhat\s+(?:\w+\s+)*(?:medicine|dosage|dose|mg|grams)\s+(?:should|can)\s+i\s+take\b",
    r"\bhow\s+(?:many|much)\s+(?:mg|grams|tablets|pills|spoons|drops)\s+(?:should|do)\s+i\s+take\b",
    r"\bprescribe\s+(?:me|something|medicine)\b",
    r"\bstop\s+(?:taking\s+)?(?:\w+\s+)*(?:medicine|pills|tablets|medication)\b",
    r"\breplace\s+(?:\w+\s+)*(?:medicine|pills|prescriptions|medication)\s+with\b",
    r"\bcure\s+(?:my\s+)?(?:cancer|diabetes|hiv|tumor|cardiac|stroke)\b",
    r"\bdiagnose\s+(?:me|my\s+condition|my\s+symptoms|this)\b",
    r"\bwhat\s+disease\s+do\s+i\s+have\b",
    # Marathi Prescription & Dosage requests
    r"\b(?:kiti|how\s+many)\s+(?:mg|gram|goli|golya|dose|tablet|tablets)\b",
    r"\bdoctoranchi\s+(?:dawa|aushadh)\s+band\s+karu\b",
    r"\b(?:prescribe|prescription)\s+(?:dya|kara)\b",
    r"\b(?:कॅन्सर|कर्करोग|मधुमेह)\s+पूर्ण\s+बरा\s+करा\b",
    r"\bकिती\s+(?:गोळ्या|डोस|मिलीग्राम)\s+(?:घ्याव्यात|घ्यावे)\b"
]

MEDICAL_DISCLAIMER_TEXT = (
    "🌿 **Educational Disclaimer**: AyurBot is an educational assistant designed to share traditional "
    "Ayurvedic principles, classical philosophies, and scientific literature. It is **not** a diagnostic "
    "tool and cannot prescribe treatments, determine personalized medical dosages, or replace qualified medical care.\n\n"
    "If you are experiencing acute symptoms, pain, or a medical emergency, please immediately consult a qualified "
    "physician, licensed Ayurvedic practitioner, or local emergency medical services."
)

class SafetyClassifier:
    """Layer 1: Input Safety Classifier & Layer 2: Output Safety Validator."""

    @staticmethod
    def classify_input(query: str, lang: str = "en") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Classifies input query.
        Returns:
            (is_safe, refusal_response, reason)
        """
        q = query.lower().strip()

        # Check for immediate emergencies
        for pattern in EMERGENCY_KEYWORDS:
            if re.search(pattern, q):
                if lang == "mr":
                    refusal = (
                        "⚠️ **तातडीची आरोग्य सूचना (Emergency Notice)**\n\n"
                        "तुमची लक्षणे तातडीच्या वैद्यकीय समस्येचे संकेत असू शकतात. "
                        "आयुर्बॉट हे केवळ शैक्षणिक साधन आहे आणि वैद्यकीय आणीबाणी हाताळू शकत नाही.\n\n"
                        "**कृपया त्वरित जवळच्या रुग्णालय, वैद्यकीय अधिकारी किंवा आपत्कालीन वैद्यकीय सेवेशी संपर्क साधा.**"
                    )
                elif lang == "hi":
                    refusal = (
                        "⚠️ **आपातकालीन स्वास्थ्य सूचना (Emergency Notice)**\n\n"
                        "आपके लक्षण किसी गंभीर या आपातकालीन स्थिति का संकेत हो सकते हैं। "
                        "आयुर्बॉट केवल एक शैक्षिक सहायक है और आपातकालीन स्थिति का समाधान नहीं कर सकता।\n\n"
                        "**कृपया तुरंत नजदीकी अस्पताल, चिकित्सक या आपातकालीन सेवा से संपर्क करें।**"
                    )
                else:
                    refusal = (
                        "⚠️ **Emergency Health Notice**\n\n"
                        "It sounds like you may be describing an acute or urgent medical situation. "
                        "AyurBot is strictly an educational tool and cannot handle medical emergencies or acute distress.\n\n"
                        "**Please immediately seek emergency medical attention or contact your local emergency services (e.g., 911, 112, or local hospital) or an on-call physician.**"
                    )
                return False, refusal, "emergency_query"

        # Check for prescription/dosage/diagnosis queries
        for pattern in PRESCRIPTION_KEYWORDS:
            if re.search(pattern, q):
                if lang == "mr":
                    refusal = (
                        "🌿 **शैक्षणिक सूचना — औषधोपचार सल्ला नाही**\n\n"
                        "मी आयुर्वेदाच्या मूलभूत संकल्पना, दिनचर्या आणि वनस्पतींबद्दल सामान्य शैक्षणिक माहिती देऊ शकतो, "
                        "परंतु मी **कोणतेही रोग निदान करू शकत नाही किंवा वैयक्तिक औषध / डोस सुचवू शकत नाही**.\n\n"
                        "तसेच, तुमच्या डॉक्टरांनी दिलेली औषधे परस्पर बंद करू नका.\n\n"
                        "कृपया वैयक्तिक उपचारांसाठी नोंदणीकृत आयुर्वेदिक वैद्य किंवा डॉक्टरांचा सल्ला घ्या."
                    )
                elif lang == "hi":
                    refusal = (
                        "🌿 **शैक्षणिक सूचना — नैदानिक परामर्श अस्वीकरण**\n\n"
                        "मैं आयुर्वेदिक सिद्धांतों और जड़ी-बूटियों के बारे में सामान्य शैक्षिक जानकारी प्रदान कर सकता हूँ, "
                        "परंतु मैं **चिकित्सीय निदान नहीं कर सकता और न ही कोई दवा या व्यक्तिगत मात्रा (dosage) निर्धारित कर सकता हूँ**।\n\n"
                        "कृपया व्यक्तिगत परामर्श के लिए किसी योग्य आयुर्वेदिक वैद्य या डॉक्टर से संपर्क करें।"
                    )
                else:
                    refusal = (
                        "🌿 **Educational Notice — Non-Diagnostic Response**\n\n"
                        "I can provide general educational information about Ayurvedic concepts, traditional herbs, and classical philosophies, "
                        "but I **cannot diagnose medical conditions, recommend personalized dosages, or prescribe medicines**.\n\n"
                        "Additionally, you should **never discontinue or alter prescribed medications** without the direct supervision of your healthcare provider.\n\n"
                        "Please consult a licensed Ayurvedic Vaidya or qualified medical doctor for personalized clinical evaluation."
                    )
                return False, refusal, "prescription_diagnosis_query"

        return True, None, None

    @staticmethod
    def validate_output(response_text: str) -> str:
        """
        Layer 2: Output Safety Validator.
        Scans generated output to ensure educational grounding and attaches educational disclaimer.
        """
        # Ensure that if the response does not already have an educational disclaimer or notes, we cleanly present it
        if "disclaimer" not in response_text.lower() and "consult" not in response_text.lower():
            response_text = response_text.strip() + "\n\n---\n*Note: This information is presented for traditional educational purposes and does not substitute for professional medical counsel.*"
        
        return response_text
