import re
from typing import Dict, List, Tuple

# Common Romanized Hindi (Hinglish) markers
HINGLISH_MARKERS = {
    "ke", "liye", "kya", "hai", "kaise", "fayde", "konsi", "konsa", "aushadhi",
    "dawa", "dawai", "hota", "hoti", "kare", "karna", "batao", "chahiye", "kaun",
    "khasi", "bukhar", "dard", "aur", "mein", "kab", "kisko", "peena", "khana"
}

# Common Romanized Marathi markers
MARATHI_MARKERS = {
    "sathi", "khokla", "khoklya", "khoklyasathi", "aahe", "kay", "kasa", "kashi",
    "kase", "karave", "sanga", "sang", "aushadh", "aushadha", "upay", "tras",
    "mhanje", "kiti", "dya", "madhe", "tulas", "halad", "avla", "gulvel",
    "kadulimb", "doke", "pot", "tap", "sardi", "ghasa", "aani", "nusti", "koni"
}

def detect_language(text: str) -> str:
    """
    Detects language based on script or vocabulary.
    Returns: 'mr' (Marathi), 'hi' (Hindi/Hinglish), 'sa' (Sanskrit), or 'en' (English).
    """
    words = set(re.findall(r"\b\w+\b", text.lower()))

    # Check for Romanized Marathi words
    marathi_overlap = words.intersection(MARATHI_MARKERS)
    if len(marathi_overlap) >= 1 and ("sathi" in words or "khokla" in words or "aushadh" in words or "upay" in words or "karave" in words or "sanga" in words or "aahe" in words):
        return "mr"

    # Check for Hinglish words
    hinglish_overlap = words.intersection(HINGLISH_MARKERS)
    if len(hinglish_overlap) >= 2 or ("konsi" in words or "aushadhi" in words or "fayde" in words):
        return "hi"

    # Devanagari Unicode Block: U+0900 to U+097F
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    total_chars = len(re.findall(r"\w", text))

    if total_chars > 0 and (devanagari_chars / total_chars) > 0.3:
        if "ः" in text or "म्" in text or "संस्कृत" in text or "इति" in text:
            return "sa"
        elif any(w in text for w in ["आहे", "काय", "करावे", "मराठी", "खोकला", "खोकल्यासाठी", "औषध", "उपाय", "साठी", "सांगा", "कसे", "त्रास", "तुळस", "हळद", "गुळवेल", "पोटदुखी", "ताप"]):
            return "mr"
        return "hi"
    return "en"

# Enhanced Ayurveda Multilingual, Marathi & Hinglish Glossary
AYURVEDA_GLOSSARY: Dict[str, List[str]] = {
    # Marathi Devanagari
    "खोकला": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi", "kapha", "pranavaha"],
    "खोकल्यासाठी": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi", "kapha"],
    "खोकल्यावर": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi"],
    "औषध": ["herbs", "dravyaguna", "formulations", "medicine", "remedies", "treatment"],
    "औषधे": ["herbs", "dravyaguna", "formulations", "medicine"],
    "उपाय": ["remedies", "chikitsa", "ayurvedic home remedies", "treatment"],
    "साठी": ["for"],
    "ताप": ["fever", "jwara", "giloy", "guduchi"],
    "सर्दी": ["cold", "rhinitis", "pratishyaya", "tulsi", "haridra"],
    "घसा": ["throat", "kantha", "yashtimadhu", "licorice"],
    "पोटदुखी": ["digestive fire", "agni", "ama", "triphala", "udarashoola"],
    "डोकेदुखी": ["headache", "shirashoola", "brahmi"],
    "सांधेदुखी": ["joint pain", "sandhivata", "vata", "ashwagandha"],
    "तुळस": ["tulsi", "holy basil", "ocimum sanctum", "kasa"],
    "ज्येष्ठमध": ["yashtimadhu", "licorice", "glycyrrhiza glabra", "kasa", "throat"],
    "सुंठ": ["shunthi", "ginger", "zingiber officinale", "deepana", "kapha"],
    "हळद": ["turmeric", "haridra", "curcuma longa"],
    "आवळा": ["amalaki", "amla", "indian gooseberry", "phyllanthus emblica"],
    "गुळवेल": ["guduchi", "giloy", "tinospora cordifolia"],
    "कडुलिंब": ["neem", "nimba", "azadirachta indica"],

    # Marathi Romanized / Phonetic
    "khokla": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi", "kapha", "pranavaha"],
    "khoklya": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi"],
    "khoklasathi": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi"],
    "khoklyasathi": ["cough", "kasa", "tulsi", "respiratory", "yashtimadhu", "sitopaladi"],
    "aushadh": ["herbs", "dravyaguna", "formulations", "medicine", "remedies"],
    "aushadha": ["herbs", "dravyaguna", "formulations", "medicine"],
    "upay": ["remedies", "chikitsa", "ayurvedic home remedies", "treatment"],
    "sathi": ["for"],
    "tap": ["fever", "jwara", "giloy", "guduchi"],
    "sardi": ["cold", "rhinitis", "pratishyaya", "tulsi", "haridra"],
    "ghasa": ["throat", "kantha", "yashtimadhu", "licorice"],
    "pot dukhi": ["digestive fire", "agni", "ama", "triphala"],
    "doke dukhi": ["headache", "shirashoola", "brahmi"],
    "sandhe dukhi": ["joint pain", "sandhivata", "vata"],
    "tulas": ["tulsi", "holy basil", "ocimum sanctum", "kasa"],
    "jyeshthamadh": ["yashtimadhu", "licorice", "glycyrrhiza glabra", "kasa"],
    "sunth": ["shunthi", "ginger", "zingiber officinale", "deepana"],
    "halad": ["turmeric", "haridra", "curcuma longa"],
    "avla": ["amalaki", "amla", "indian gooseberry"],
    "gulvel": ["guduchi", "giloy", "tinospora cordifolia"],
    "kadulimb": ["neem", "nimba", "azadirachta indica"],

    # Women's Menstrual Health, Period Cycle & Gynecology
    "period": ["period", "menstrual", "menstruation", "artava", "rajaswala paricharya", "apana vayu", "shatavari", "ashoka", "cycle"],
    "periods": ["period", "menstrual", "menstruation", "artava", "rajaswala paricharya", "apana vayu", "shatavari", "ashoka", "cycle"],
    "menstrual": ["menstrual", "menstruation", "artava", "rajaswala paricharya", "apana vayu", "shatavari", "ashoka", "cycle", "cramps"],
    "menstruation": ["menstruation", "artava", "rajaswala paricharya", "apana vayu", "shatavari", "ashoka", "menstrual cycle"],
    "menses": ["menses", "artava", "rajaswala paricharya", "apana vayu", "shatavari", "ashoka"],
    "cramps": ["menstrual cramps", "kashtartava", "dysmenorrhea", "apana vayu", "shatavari", "ashoka", "jeera", "ajwain"],
    "pms": ["pms", "premenstrual", "artava", "shatavari", "pitta", "vata"],
    "shatavari": ["shatavari", "asparagus racemosus", "stri rasayana", "artava", "stanya"],
    "ashoka": ["ashoka", "saraca asoca", "uterine tonic", "artava", "ashokarishta", "menstrual"],
    "मासिक पाळी": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka", "apana vayu"],
    "मासिक धर्म": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka", "apana vayu"],
    "मासिक": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka"],
    "पीरियड्स": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka", "apana vayu"],
    "पीरियड": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka", "apana vayu"],
    "माहवारी": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka", "apana vayu"],
    "कष्टार्तव": ["menstrual cramps", "kashtartava", "dysmenorrhea", "rajaswala paricharya", "apana vayu", "shatavari", "ashoka"],
    "पाळी": ["period", "menstrual", "artava", "rajaswala paricharya", "shatavari", "ashoka"],
    "शतावरी": ["shatavari", "asparagus racemosus", "artava", "stanya", "rasayana"],
    "अशोक": ["ashoka", "saraca asoca", "uterine tonic", "artava"],

    # Hindi Devanagari & Classical terms
    "त्रिदोष": ["tridosha", "three doshas", "doshas"],
    "वात": ["vata", "vayu", "wind"],
    "पित्त": ["pitta", "fire", "metabolism"],
    "कफ": ["kapha", "water and earth", "mucus"],
    "प्रकृति": ["prakriti", "body constitution", "baseline"],
    "विकृति": ["vikriti", "imbalance"],
    "अग्नि": ["agni", "digestive fire", "jatharagni"],
    "आम": ["ama", "undigested toxins", "metabolic waste"],
    "पंचमहाभूत": ["panchamahabhuta", "five elements", "akasha vayu agni jala prithvi"],
    "दिनचर्या": ["dinacharya", "daily regimen", "morning routine"],
    "ऋतुचर्या": ["ritucharya", "seasonal regimen"],
    "आहार": ["ahara", "food", "diet"],
    "निद्रा": ["nidra", "sleep"],
    "षड्रस": ["shad rasa", "six tastes"],
    "विरुद्ध आहार": ["viruddha ahara", "incompatible foods"],
    "धातु": ["dhatus", "sapta dhatus", "seven tissues"],
    "तुलसी": ["tulsi", "holy basil", "ocimum sanctum", "kasa"],
    "अश्वगंधा": ["ashwagandha", "withania somnifera", "indian ginseng"],
    "आमलकी": ["amalaki", "amla", "indian gooseberry"],
    "हल्दी": ["turmeric", "haridra", "curcuma longa"],
    "नीम": ["neem", "nimba", "azadirachta indica"],
    "त्रिफला": ["triphala", "haritaki bibhitaki amalaki"],
    "गिलोय": ["giloy", "guduchi", "tinospora cordifolia"],
    "खांसी": ["cough", "kasa", "tulsi", "respiratory", "sitopaladi"],
    
    # Hinglish & Romanized equivalents
    "khasi": ["kasa", "respiratory", "tulsi", "cough", "sitopaladi"],
    "khasa": ["kasa", "cough", "tulsi"],
    "aushadhi": ["herbs", "dravyaguna", "formulations", "medicine"],
    "dawa": ["herbs", "dravyaguna", "formulations", "medicine"],
    "fayde": ["benefits", "traditional uses", "indications"],
    "bukhar": ["jwara", "fever", "giloy", "guduchi"],
    "pet dard": ["digestive fire", "agni", "ama"],
    "neend": ["nidra", "sleep", "ashwagandha"],
    "kamzori": ["balya", "rejuvenation", "ashwagandha"]
}

def expand_multilingual_query(query: str) -> str:
    """
    Expands a Marathi, Hindi, or Sanskrit query with English Ayurvedic transliterations
    to maximize hybrid vector and BM25 retrieval accuracy against the corpus.
    """
    expanded_terms = [query]
    q_lower = query.lower()
    
    for term, eng_synonyms in AYURVEDA_GLOSSARY.items():
        if term.lower() in q_lower:
            expanded_terms.extend(eng_synonyms)

    return " ".join(expanded_terms)

def get_language_instructions(target_lang: str) -> str:
    """Provides system prompt instructions based on selected target language."""
    if target_lang == "mr":
        return (
            "IMPORTANT MULTILINGUAL INSTRUCTION:\n"
            "The user selected or asked in Marathi (मराठी).\n"
            "You MUST generate the ENTIRE response in natural, fluent, and polite Marathi (मराठी भाषा) in Devanagari script.\n"
            "Translate all concepts, descriptions, headings, bullet points, and disclaimers into Marathi.\n"
            "Include traditional Ayurvedic terms (उदा. कास, कफ, वात, पित्त, तुळस, ज्येष्ठमध, दिनचर्या, इ.) with clear Marathi explanation.\n"
            "Structure the response with clear Marathi headings (उदा. ### मुख्य आयुर्वेदिक माहिती, #### पारंपारिक उपाय, ### महत्त्वाची शैक्षणिक सूचना).\n"
            "Do NOT respond in English."
        )
    elif target_lang == "hi":
        return (
            "IMPORTANT MULTILINGUAL INSTRUCTION:\n"
            "The user asked in Hindi (हिन्दी) or requested Hindi responses. "
            "Please respond completely in clear, natural Hindi (हिन्दी भाषा), "
            "using standard Ayurvedic Devanagari terminology (जैसे: वात, पित्त, कफ, दिनचर्या, प्रकृति, अग्नि, आदि). "
            "Include the sources and disclaimer in Hindi."
        )
    elif target_lang == "sa":
        return (
            "IMPORTANT MULTILINGUAL INSTRUCTION:\n"
            "The user requested Sanskrit (संस्कृतम्). "
            "Please provide an educational explanation in Sanskrit or bilingual Sanskrit-Hindi/English, "
            "featuring classical shlokas and definitions where applicable."
        )
    elif target_lang == "gu":
        return (
            "IMPORTANT MULTILINGUAL INSTRUCTION:\n"
            "The user requested Gujarati (ગુજરાતી). Please respond in clear Gujarati script with standard Ayurvedic terms."
        )
    elif target_lang == "ta":
        return (
            "IMPORTANT MULTILINGUAL INSTRUCTION:\n"
            "The user requested Tamil (தமிழ்). Please respond in clear Tamil script with standard Ayurvedic/Siddha concepts."
        )
    elif target_lang == "te":
        return (
            "IMPORTANT MULTILINGUAL INSTRUCTION:\n"
            "The user requested Telugu (తెలుగు). Please respond in clear Telugu script with standard Ayurvedic terms."
        )
    else:
        return (
            "Language: English. Respond in clear, educational English, referencing Sanskrit terms in transliteration."
        )
