import re
import difflib
from typing import Dict, List, Tuple, Set, Optional

# Words that should NEVER be fuzzy-corrected or modified
PRESERVED_WORDS: Set[str] = {
    # English common words & query phrasing
    "what", "is", "are", "the", "a", "an", "and", "or", "in", "of", "to", "for",
    "with", "on", "at", "by", "from", "as", "into", "its", "it", "this", "that",
    "which", "who", "whom", "can", "how", "explain", "describe", "about", "tell",
    "me", "give", "please", "some", "any", "help", "my", "i", "have", "has", "had",
    "do", "does", "did", "be", "been", "being", "so", "not", "no", "why", "where",
    "when", "take", "taking", "use", "using", "good", "bad", "best", "like", "more",
    "rules", "tips", "types", "effects", "side", "difference", "meaning", "name",
    
    # Hindi / Hinglish functional words
    "kya", "hai", "hain", "ho", "tha", "thi", "the", "ka", "ki", "ke", "ko", "se",
    "me", "mein", "par", "aur", "ya", "yaa", "nahi", "mat", "kaise", "kyu", "kyun",
    "kis", "kisko", "kise", "kaun", "konsa", "konsi", "konse", "batao", "bataiye",
    "chahiye", "karna", "kare", "karo", "hota", "hoti", "hote", "le", "lu", "len",
    "lena", "lo", "mujhe", "hum", "aap", "tum", "sab", "sabhi", "peena", "khana",
    "lag", "raha", "rahi", "rahe", "hoga", "hogi", "hoge", "apna", "apne", "apni",
    "kuch", "bahut", "jyada", "kam", "waqt", "samay", "din", "raat",
    
    # Marathi functional words
    "kay", "aahe", "ahet", "ahe", "kasa", "kashi", "kase", "sanga", "sang",
    "karave", "kara", "dya", "dyave", "sathi", "mule", "madhe", "var", "vr",
    "aani", "ani", "tar", "mag", "koni", "konala", "kiti", "mala", "amhala",
    "tumhi", "apan", "ghyava", "ghyave", "khava", "peeva", "hota", "hoti",
    "hote", "nusti", "tras", "hoto", "hote"
}

# Core canonical Ayurvedic concepts and entities
CANONICAL_AYURVEDA_TERMS: Dict[str, Dict[str, any]] = {
    # Ayurveda Definition & Overview
    "ayurveda": {
        "canonical": "What is Ayurveda — Origin and Definition",
        "category": "Fundamentals",
        "synonyms": ["science of life", "traditional medicine", "ayurvedic medicine", "holistic health"],
        "keywords": ["swastha", "charaka", "sushruta", "definition", "origin", "samadosha", "principles"],
        "patterns": ["ayurveda", "auredik", "aurvedik", "ayurvdik", "auredic", "aurvedic", "ayurwedic", "ayurbedic", "ayurvda", "aureda", "ayurwed", "ayurved", "ayurvedic", "आयुर्वेद", "आयुर्वेदिक"]
    },

    # Herbs & Formulations
    "tulsi": {
        "canonical": "Tulsi (Holy Basil) — Ocimum sanctum",
        "category": "Herbs",
        "synonyms": ["holy basil", "ocimum sanctum", "tulas", "tulasi"],
        "keywords": ["respiratory", "kasa", "cough", "pranavaha", "kapha", "fever", "throat"],
        "patterns": ["tulsi", "tulsee", "tulsii", "thulsi", "tulsy", "tulas", "tulasi", "तुलसी", "तुलसि", "तुळस"]
    },
    "ashwagandha": {
        "canonical": "Ashwagandha (Indian Ginseng) — Withania somnifera",
        "category": "Herbs",
        "synonyms": ["withania somnifera", "indian ginseng", "asgandh"],
        "keywords": ["stress", "sleep", "nidra", "strength", "balya", "rasayana", "vata", "nervous system", "endurance", "cortisol"],
        "patterns": ["ashwagandha", "aswagandha", "ashwaganda", "aswaganda", "ashwaghandha", "aswaghandha", "asvagandha", "ashvagandha", "ashwgandha", "अश्वगंधा", "अश्वगंध"]
    },
    "triphala": {
        "canonical": "Triphala — The Classical Three-Fruit Synergy",
        "category": "Herbs",
        "synonyms": ["three fruits", "triphala churna"],
        "keywords": ["digestion", "bowel", "constipation", "haritaki", "bibhitaki", "amalaki", "anulomana", "tridoshic", "gut"],
        "patterns": ["triphala", "triphla", "trifala", "trifla", "thriphala", "triphala churna", "triphla churna", "त्रिफला", "त्रिफळा"]
    },
    "amalaki": {
        "canonical": "Amalaki / Amla (Indian Gooseberry) — Phyllanthus emblica",
        "category": "Herbs",
        "synonyms": ["amla", "indian gooseberry", "phyllanthus emblica", "emblica officinalis"],
        "keywords": ["vitamin c", "rasayana", "pitta", "cooling", "hair", "eyes", "chakshushya", "antioxidant"],
        "patterns": ["amalaki", "amalki", "amla", "avla", "aawla", "amalkee", "amlaki", "आमलकी", "आंवला", "आवळा"]
    },
    "haridra": {
        "canonical": "Haridra / Turmeric — Curcuma longa",
        "category": "Herbs",
        "synonyms": ["turmeric", "haldi", "halad", "curcuma longa"],
        "keywords": ["curcumin", "anti-inflammatory", "skin", "kushtha", "varnya", "detox", "blood", "curcuminoids"],
        "patterns": ["haridra", "haldi", "halad", "haldii", "haridraa", "turmeric", "हल्दी", "हळद", "हरिद्रा"]
    },
    "guduchi": {
        "canonical": "Guduchi / Giloy — Tinospora cordifolia",
        "category": "Herbs",
        "synonyms": ["giloy", "amrita", "tinospora cordifolia"],
        "keywords": ["immunity", "fever", "jwara", "vyadhikshamatva", "rasayana", "pitta", "blood purifier"],
        "patterns": ["guduchi", "gudusi", "giloy", "giloi", "geloy", "guducci", "amrita", "गिलोय", "गिलोई", "गुडूची", "गुळवेल"]
    },
    "yashtimadhu": {
        "canonical": "Yashtimadhu / Licorice (Jyeshthamadh / Mulethi) — Glycyrrhiza glabra",
        "category": "Herbs",
        "synonyms": ["licorice", "mulethi", "jyeshthamadh", "glycyrrhiza glabra"],
        "keywords": ["cough", "kasa", "throat", "kantha", "vocal", "gastric", "ulcer", "soothing"],
        "patterns": ["yashtimadhu", "yastimadhu", "yashtimadh", "yashthimadhu", "jyeshthamadh", "jyesthimadh", "jeshtamadhu", "jeshtamadh", "mulethi", "muleti", "mulaithi", "licorice", "मुलेठी", "ज्येष्ठमध", "यष्टिमधु"]
    },
    "neem": {
        "canonical": "Neem (Nimba) — Azadirachta indica",
        "category": "Herbs",
        "synonyms": ["nimba", "azadirachta indica"],
        "keywords": ["skin", "cooling", "pitta", "blood purifier", "raktashodhaka", "krimighna", "bitter", "acne"],
        "patterns": ["neem", "nimba", "kadulimb", "nimb", "नीम", "कडुलिंब", "निंब"]
    },
    "brahmi": {
        "canonical": "Brahmi / Bacopa — Bacopa monnieri",
        "category": "Herbs",
        "synonyms": ["bacopa monnieri", "medhya rasayana"],
        "keywords": ["memory", "brain", "intellect", "dhi", "dhriti", "smriti", "anxiety", "mind", "focus"],
        "patterns": ["brahmi", "bhrami", "brahami", "bacopa", "ब्राह्मी"]
    },
    "shatavari": {
        "canonical": "Shatavari (Stri Rasayana) — Asparagus racemosus",
        "category": "Herbs",
        "synonyms": ["asparagus racemosus", "stri rasayana"],
        "keywords": ["women health", "reproductive", "pitta", "cooling", "hormonal", "stanya", "menstrual", "period", "artava"],
        "patterns": ["shatavari", "satavari", "shatavri", "satavri", "shathavari", "शतावरी"]
    },
    "ashoka": {
        "canonical": "Ashoka (Uterine Tonic) — Saraca asoca",
        "category": "Herbs",
        "synonyms": ["saraca asoca", "uterine tonic"],
        "keywords": ["menstrual", "period", "artava", "cramps", "uterine", "bleeding", "dysmenorrhea"],
        "patterns": ["ashoka", "asoka", "ashok", "asok", "अशोक"]
    },
    "shunthi": {
        "canonical": "Shunthi / Dry Ginger (Sunth) — Zingiber officinale",
        "category": "Herbs",
        "synonyms": ["dry ginger", "sunth", "sonth", "zingiber officinale"],
        "keywords": ["digestive fire", "agni", "kapha", "vata", "deepana", "pachana", "nausea", "bloating"],
        "patterns": ["shunthi", "sunthi", "sunth", "sonth", "soonth", "dry ginger", "ginger", "सुंठ", "सोंठ"]
    },
    "sitopaladi": {
        "canonical": "Sitopaladi Churna — Classical Formulation for Cough, Cold & Respiratory Balance",
        "category": "Herbs",
        "synonyms": ["sitopaladi formulation"],
        "keywords": ["cough", "cold", "respiratory", "kasa", "kapha", "pranavaha", "fever", "congestion"],
        "patterns": ["sitopaladi", "sitopladi", "sitopiladi", "sitopaladi churna", "sitopladi churn", "सितोपलादि", "सितोपलादि चूर्ण"]
    },
    "chyawanprash": {
        "canonical": "Chyawanprash — The Premier Classical Rasayana Formulation",
        "category": "Herbs",
        "synonyms": ["chyavanprash", "rasayana jam"],
        "keywords": ["immunity", "amalaki", "rejuvenation", "ojas", "vitality", "longevity"],
        "patterns": ["chyawanprash", "chyavanprash", "chywanprash", "chyawanprasha", "च्यवनप्राश"]
    },

    # Doshas & Bio-energies
    "tridosha": {
        "canonical": "Tridosha Theory — Overview of the Three Bio-energies",
        "category": "Doshas",
        "synonyms": ["three bio-energies", "three doshas", "vata pitta kapha"],
        "keywords": ["vata", "pitta", "kapha", "equilibrium", "constitution", "doshic"],
        "patterns": ["tridosha", "tridosh", "tridoshas", "tridosham", "tridoshaa", "3 doshas", "three doshas", "त्रिदोष"]
    },
    "vata": {
        "canonical": "Vata Dosha — Characteristics, Functions, and Qualities",
        "category": "Doshas",
        "synonyms": ["vayu", "wind", "air and space"],
        "keywords": ["movement", "circulation", "dryness", "nervous system", "joint pain", "constipation", "insomnia", "mobility"],
        "patterns": ["vata", "vat", "vaat", "vatha", "waat", "wata", "वात", "वायु"]
    },
    "pitta": {
        "canonical": "Pitta Dosha — Characteristics, Functions, and Qualities",
        "category": "Doshas",
        "synonyms": ["fire and water", "bile", "metabolic energy"],
        "keywords": ["metabolism", "digestion", "heat", "acidity", "inflammation", "liver", "skin", "transformation"],
        "patterns": ["pitta", "pit", "pitt", "pitha", "pittah", "पित्त"]
    },
    "kapha": {
        "canonical": "Kapha Dosha — Characteristics, Functions, and Qualities",
        "category": "Doshas",
        "synonyms": ["water and earth", "phlegm", "structural energy"],
        "keywords": ["structure", "lubrication", "stability", "mucus", "weight", "congestion", "cold", "cough"],
        "patterns": ["kapha", "kuf", "kuff", "kafa", "kapfa", "khapa", "kaph", "कफ", "कफ़"]
    },

    # Fundamentals & Principles
    "prakriti": {
        "canonical": "Prakriti and Vikriti — Individual Constitution vs Current Imbalance",
        "category": "Fundamentals",
        "synonyms": ["body constitution", "genetic constitution", "baseline doshas"],
        "keywords": ["constitution", "innate balance", "vikriti", "body type", "assessment", "baseline"],
        "patterns": ["prakriti", "prakruti", "prakrity", "prakrti", "parkriti", "prakruti type", "body constitution", "प्रकृति", "प्रकृती"]
    },
    "vikriti": {
        "canonical": "Prakriti and Vikriti — Individual Constitution vs Current Imbalance",
        "category": "Fundamentals",
        "synonyms": ["current state of imbalance", "doshic disturbance"],
        "keywords": ["imbalance", "disease", "dosha imbalance", "deviation"],
        "patterns": ["vikriti", "vikruti", "vikrity", "vikrti", "विकृति", "विकृती"]
    },
    "agni": {
        "canonical": "Agni — The Metabolic and Digestive Fire",
        "category": "Fundamentals",
        "synonyms": ["jatharagni", "digestive fire", "metabolism"],
        "keywords": ["digestion", "metabolism", "gut", "sama agni", "mandagni", "tikshnagni", "vishamagni", "digestive warmth"],
        "patterns": ["agni", "jatharagni", "aagni", "digestive fire", "अग्नि", "जठराग्नि"]
    },
    "ama": {
        "canonical": "Ama — Undigested Toxic Residue and Metabolic Impurities",
        "category": "Fundamentals",
        "synonyms": ["endotoxins", "undigested food residue"],
        "keywords": ["toxins", "coating on tongue", "sluggishness", "indigestion", "clogged channels", "srotas"],
        "patterns": ["ama", "aam", "aama", "amadosha", "आम", "आमदोष"]
    },
    "panchamahabhuta": {
        "canonical": "Panchamahabhuta — The Five Great Elements",
        "category": "Fundamentals",
        "synonyms": ["five great elements", "pancha mahabhutas"],
        "keywords": ["akasha", "vayu", "tejas", "jala", "prithvi", "space", "air", "fire", "water", "earth"],
        "patterns": ["panchamahabhuta", "panchamahabhutas", "panch mahabhuta", "5 elements", "five elements", "पंचमहाभूत"]
    },
    "dhatus": {
        "canonical": "Sapta Dhatus — The Seven Vital Bodily Tissues",
        "category": "Fundamentals",
        "synonyms": ["seven tissues", "sapta dhatu"],
        "keywords": ["rasa", "rakta", "mamsa", "meda", "asthi", "majja", "shukra", "ojas", "tissue nutrition"],
        "patterns": ["dhatu", "dhatus", "sapta dhatu", "saptadhatu", "sapta dhatus", "7 dhatus", "धातु", "सप्तधातु"]
    },
    "ojas": {
        "canonical": "Ojas — Vital Essence and Immunity",
        "category": "Fundamentals",
        "synonyms": ["vital essence", "immunity essence"],
        "keywords": ["immunity", "vitality", "glow", "strength", "radiance", "ojas"],
        "patterns": ["ojas", "ojus", "oja", "ओजस", "ओज"]
    },

    # Lifestyle & Regimen
    "dinacharya": {
        "canonical": "Dinacharya — The Daily Health Routine",
        "category": "Lifestyle",
        "synonyms": ["daily regimen", "ayurvedic routine", "morning routine"],
        "keywords": ["brahma muhurta", "tongue scraping", "oil pulling", "abhyanga", "snana", "vyayama", "daily habits"],
        "patterns": ["dinacharya", "dincharya", "dincharyaa", "dinchariya", "dinacharyaa", "dina charya", "daily routine", "दिनचर्या"]
    },
    "ritucharya": {
        "canonical": "Ritucharya — Seasonal Regimen for Year-round Health",
        "category": "Lifestyle",
        "synonyms": ["seasonal regimen", "seasonal routine"],
        "keywords": ["seasons", "monsoon", "varsha", "shishira", "vasanta", "grishma", "sharad", "hemanta", "diet per season"],
        "patterns": ["ritucharya", "rituchrya", "rtucharya", "rutucharya", "rituchariya", "ritu charya", "seasonal regimen", "ऋतुचर्या"]
    },
    "viruddha_ahara": {
        "canonical": "Viruddha Ahara — Incompatible Food Combinations",
        "category": "Lifestyle",
        "synonyms": ["incompatible food combinations", "food combining"],
        "keywords": ["milk and sour fruits", "fish and milk", "honey and ghee", "toxins", "indigestion", "skin allergy"],
        "patterns": ["viruddha ahara", "viruddhahara", "viruddha ahar", "virudha ahar", "virudh ahar", "virudha ahara", "incompatible foods", "food combination", "विरुद्ध आहार"]
    },
    "panchakarma": {
        "canonical": "Panchakarma — Five Classical Detoxification Procedures",
        "category": "Lifestyle",
        "synonyms": ["five cleansing procedures", "detoxification therapy"],
        "keywords": ["vamana", "virechana", "basti", "nasya", "raktamokshana", "shodhana", "deep cleansing"],
        "patterns": ["panchakarma", "panchkarma", "panchakarmma", "panch karma", "panchakarma therapy", "पंचकर्म"]
    },
    "ahara": {
        "canonical": "Ahara — Ayurvedic Principles of Food and Nutrition",
        "category": "Lifestyle",
        "synonyms": ["ayurvedic diet", "nutrition", "satvik food"],
        "keywords": ["six tastes", "shad rasa", "diet rules", "eating habits", "fresh food"],
        "patterns": ["ahara", "aahar", "ahar", "ayurvedic diet", "आहार"]
    },
    "nidra": {
        "canonical": "Nidra — The Science of Ayurvedic Sleep and Rest",
        "category": "Lifestyle",
        "synonyms": ["sleep hygiene", "ayurvedic sleep"],
        "keywords": ["insomnia", "anidra", "sleep posture", "night routine", "foot massage", "pada abhyanga"],
        "patterns": ["nidra", "nindra", "neend", "nind", "sleep", "insomnia", "anidra", "निद्रा", "नींद"]
    },
    "abhyanga": {
        "canonical": "Abhyanga — The Art and Practice of Warm Oil Self-Massage",
        "category": "Lifestyle",
        "synonyms": ["oil massage", "body massage"],
        "keywords": ["sesame oil", "vata pacification", "lymphatic circulation", "relaxation", "skin tone"],
        "patterns": ["abhyanga", "abhyang", "abhyangam", "oil massage", "अभ्यंग"]
    },
    "rajaswala": {
        "canonical": "Rajaswala Paricharya — Classical Ayurvedic Care During Menstruation",
        "category": "Lifestyle",
        "synonyms": ["ayurvedic period regimen", "menstrual health"],
        "keywords": ["periods", "cramps", "menstruation", "artava", "apana vayu", "rest", "shatavari", "ashoka", "kashtartava"],
        "patterns": ["rajaswala", "rajaswala paricharya", "period", "periods", "perid", "priod", "menstrual", "menstruation", "menses", "cramp", "cramps", "मासिक पाळी", "मासिक धर्म", "पीरियड्स", "माहवारी"]
    },

    # Classical Texts
    "classical_texts": {
        "canonical": "Brihat Trayi — The Great Classical Ayurvedic Treatises",
        "category": "Traditional Concepts",
        "synonyms": ["brihat trayi", "laghu trayi", "charaka samhita", "sushruta samhita", "ashtanga hridaya"],
        "keywords": ["charaka", "sushruta", "vagbhata", "sharangadhara", "bhavaprakasha", "ancient texts"],
        "patterns": ["brihat trayi", "charaka", "sushruta", "vagbhata", "ashtanga hridaya", "ashtanga sangraha", "samhita", "चरक", "सुश्रुत", "वाग्भट", "बृहत्त्रयी"]
    }
}

# Direct word-level corrections for common phonetic transliterations and typos
EXACT_TYPO_MAP: Dict[str, str] = {
    # Ayurveda terms
    "auredik": "ayurvedic",
    "aurvedik": "ayurvedic",
    "ayurvdik": "ayurvedic",
    "auredic": "ayurvedic",
    "aurvedic": "ayurvedic",
    "ayurwedic": "ayurvedic",
    "ayurbedic": "ayurvedic",
    "ayurvda": "ayurveda",
    "aureda": "ayurveda",
    "ayurwed": "ayurveda",
    "ayurved": "ayurveda",
    "ayur": "ayurveda",

    # Herbs & Formulations
    "aswagandha": "ashwagandha",
    "ashwaganda": "ashwagandha",
    "aswaganda": "ashwagandha",
    "ashwaghandha": "ashwagandha",
    "aswaghandha": "ashwagandha",
    "asvagandha": "ashwagandha",
    "ashwgandha": "ashwagandha",
    "asgandh": "ashwagandha",
    "tulsee": "tulsi",
    "tulsii": "tulsi",
    "thulsi": "tulsi",
    "tulsy": "tulsi",
    "tulas": "tulsi",
    "tulasi": "tulsi",
    "triphla": "triphala",
    "trifala": "triphala",
    "trifla": "triphala",
    "thriphala": "triphala",
    "triphlaa": "triphala",
    "amalki": "amalaki",
    "amalkee": "amalaki",
    "amlaki": "amalaki",
    "avla": "amla",
    "aawla": "amla",
    "haldii": "haldi",
    "halad": "turmeric",
    "giloi": "giloy",
    "geloy": "giloy",
    "gudusi": "guduchi",
    "yastimadhu": "yashtimadhu",
    "yashtimadh": "yashtimadhu",
    "yashthimadhu": "yashtimadhu",
    "jyeshthamadh": "yashtimadhu",
    "jyesthimadh": "yashtimadhu",
    "jeshtamadhu": "yashtimadhu",
    "jeshtamadh": "yashtimadhu",
    "muleti": "mulethi",
    "mulaithi": "mulethi",
    "satavari": "shatavari",
    "shatavri": "shatavari",
    "satavri": "shatavari",
    "asoka": "ashoka",
    "ashok": "ashoka",
    "asok": "ashoka",
    "sunthi": "shunthi",
    "sunth": "shunthi",
    "sonth": "shunthi",
    "soonth": "shunthi",
    "sitopladi": "sitopaladi",
    "sitopiladi": "sitopaladi",
    "chyavanprash": "chyawanprash",
    "chywanprash": "chyawanprash",
    "bhrami": "brahmi",
    "brahami": "brahmi",
    "kadulimb": "neem",
    "nimba": "neem",

    # Doshas
    "vaat": "vata",
    "vat": "vata",
    "vatha": "vata",
    "waat": "vata",
    "wata": "vata",
    "pitt": "pitta",
    "pit": "pitta",
    "pitha": "pitta",
    "pittah": "pitta",
    "kuff": "kapha",
    "kuf": "kapha",
    "kafa": "kapha",
    "kapfa": "kapha",
    "khapa": "kapha",
    "kaph": "kapha",
    "tridosh": "tridosha",
    "tridoshas": "tridosha",
    "tridosham": "tridosha",

    # Fundamentals & Lifestyle
    "prakruti": "prakriti",
    "prakrity": "prakriti",
    "prakrti": "prakriti",
    "parkriti": "prakriti",
    "vikruti": "vikriti",
    "vikrity": "vikriti",
    "vikrti": "vikriti",
    "dincharya": "dinacharya",
    "dincharyaa": "dinacharya",
    "dinchariya": "dinacharya",
    "rtucharya": "ritucharya",
    "rituchrya": "ritucharya",
    "rutucharya": "ritucharya",
    "viruddh": "viruddha",
    "virudh": "viruddha",
    "virudha": "viruddha",
    "panchkarma": "panchakarma",
    "panchakarmma": "panchakarma",
    "abhyang": "abhyanga",
    "abhyangam": "abhyanga",
    "jatharagni": "agni",
    "aagni": "agni",
    "aam": "ama",
    "aama": "ama",
    "saptadhatu": "dhatus",
    "ojus": "ojas",

    # Symptoms, Conditions & Remedy words
    "khasi": "cough",
    "khaasi": "cough",
    "khansi": "cough",
    "kasi": "cough",
    "khokla": "cough",
    "khoklya": "cough",
    "khoklasathi": "cough remedies",
    "khoklyasathi": "cough remedies",
    "sardi": "cold",
    "surdi": "cold",
    "jukham": "cold",
    "zukam": "cold",
    "zukaam": "cold",
    "bukhar": "fever",
    "bhukhar": "fever",
    "buxar": "fever",
    "taap": "fever",
    "tap": "fever",
    "potdukhi": "stomach pain",
    "petdard": "stomach pain",
    "sardard": "headache",
    "sirdard": "headache",
    "dokedukhi": "headache",
    "sandhedukhi": "joint pain",
    "gathiya": "arthritis",
    "asidity": "acidity",
    "aciditi": "acidity",
    "kabz": "constipation",
    "kabaj": "constipation",
    "kabjit": "constipation",
    "kamzori": "weakness",
    "kamjori": "weakness",
    "thakan": "fatigue",
    "neend": "sleep",
    "nind": "sleep",
    "anidra": "insomnia",
    "tanav": "stress",
    "tanaav": "stress",
    "chinta": "anxiety",
    "khujli": "skin itching",
    "kujli": "skin itching",
    "twacha": "skin",
    "perid": "period",
    "priod": "period",
    "periods": "period",
    "pali": "period",
    "paali": "period",
    "mahvari": "period",
    "mahavari": "period",
    "shugar": "diabetes",
    "motapa": "obesity",
    "vajan": "weight",
    "dwa": "medicine",
    "dwai": "medicine",
    "davai": "medicine",
    "dawa": "medicine",
    "dawai": "medicine",
    "aushad": "aushadhi",
    "aushada": "aushadhi",
    "aushadha": "aushadhi",
    "ilaj": "treatment",
    "ilaaj": "treatment",
    "upaye": "upay",
    "upaay": "upay",
    "nuskhe": "remedies",
    "nuske": "remedies",
    "fyde": "benefits",
    "faide": "benefits",
    "faida": "benefits",
    "fayde": "benefits",
    "fayda": "benefits",
    "labh": "benefits",
    "laabh": "benefits"
}

# Multi-word phrase mapping
MULTI_WORD_PHRASES: Dict[str, Dict[str, any]] = {
    "virudha ahar": {"canonical": "Viruddha Ahara — Incompatible Food Combinations", "expansion": "viruddha ahara incompatible food combinations"},
    "virudh ahar": {"canonical": "Viruddha Ahara — Incompatible Food Combinations", "expansion": "viruddha ahara incompatible food combinations"},
    "viruddha ahar": {"canonical": "Viruddha Ahara — Incompatible Food Combinations", "expansion": "viruddha ahara incompatible food combinations"},
    "virudha ahara": {"canonical": "Viruddha Ahara — Incompatible Food Combinations", "expansion": "viruddha ahara incompatible food combinations"},
    "pet me dard": {"canonical": "Agni — The Metabolic and Digestive Fire", "expansion": "stomach pain agni ama digestion digestive fire"},
    "pet dard": {"canonical": "Agni — The Metabolic and Digestive Fire", "expansion": "stomach pain agni ama digestion digestive fire"},
    "pot dukhi": {"canonical": "Agni — The Metabolic and Digestive Fire", "expansion": "potdukhi agni ama digestion triphala"},
    "sar dard": {"canonical": "Brahmi / Bacopa — Bacopa monnieri", "expansion": "headache shirashoola brahmi stress"},
    "sir dard": {"canonical": "Brahmi / Bacopa — Bacopa monnieri", "expansion": "headache shirashoola brahmi stress"},
    "doke dukhi": {"canonical": "Brahmi / Bacopa — Bacopa monnieri", "expansion": "headache shirashoola brahmi"},
    "sandhe dukhi": {"canonical": "Vata Dosha — Characteristics, Functions, and Qualities", "expansion": "joint pain sandhivata vata ashwagandha"},
    "jodon ka dard": {"canonical": "Vata Dosha — Characteristics, Functions, and Qualities", "expansion": "joint pain sandhivata vata ashwagandha"},
    "ghutno ka dard": {"canonical": "Vata Dosha — Characteristics, Functions, and Qualities", "expansion": "joint pain sandhivata vata ashwagandha"},
    "khasi ki dawa": {"canonical": "Sitopaladi Churna — Classical Formulation for Cough, Cold & Respiratory Balance", "expansion": "cough kasa tulsi sitopaladi yashtimadhu"},
    "khasi ke upay": {"canonical": "Sitopaladi Churna — Classical Formulation for Cough, Cold & Respiratory Balance", "expansion": "cough kasa tulsi sitopaladi yashtimadhu"},
    "khokla sathi": {"canonical": "Yashtimadhu / Licorice (Jyeshthamadh / Mulethi) — Glycyrrhiza glabra", "expansion": "cough kasa tulsi sitopaladi yashtimadhu"},
    "khoklya sathi": {"canonical": "Yashtimadhu / Licorice (Jyeshthamadh / Mulethi) — Glycyrrhiza glabra", "expansion": "cough kasa tulsi sitopaladi yashtimadhu"},
    "sardi khansi": {"canonical": "Sitopaladi Churna — Classical Formulation for Cough, Cold & Respiratory Balance", "expansion": "cold cough pratishyaya kasa tulsi sitopaladi"},
    "sardi jukham": {"canonical": "Tulsi (Holy Basil) — Ocimum sanctum", "expansion": "cold pratishyaya tulsi haridra shunthi"},
    "weight loss": {"canonical": "Triphala — The Classical Three-Fruit Synergy", "expansion": "obesity medoroga triphala agni metabolism"},
    "hair fall": {"canonical": "Amalaki / Amla (Indian Gooseberry) — Phyllanthus emblica", "expansion": "hair fall khalitya amalaki amla bhringraj"},
    "baal jhadna": {"canonical": "Amalaki / Amla (Indian Gooseberry) — Phyllanthus emblica", "expansion": "hair fall khalitya amalaki amla"},
    "period cramps": {"canonical": "Rajaswala Paricharya — Classical Ayurvedic Care During Menstruation", "expansion": "menstrual cramps kashtartava shatavari ashoka apana vayu"},
    "auredik dawa": {"canonical": "What is Ayurveda — Origin and Definition", "expansion": "ayurvedic medicine herbs dravyaguna"},
    "auredik upay": {"canonical": "What is Ayurveda — Origin and Definition", "expansion": "ayurvedic remedies principles"},
    "auredik tips": {"canonical": "Dinacharya — The Daily Health Routine", "expansion": "ayurvedic fundamentals dinacharya lifestyle daily routine"},
    "aurvedik tips": {"canonical": "Dinacharya — The Daily Health Routine", "expansion": "ayurvedic fundamentals dinacharya lifestyle daily routine"},
    "aurvedik upay": {"canonical": "What is Ayurveda — Origin and Definition", "expansion": "ayurvedic remedies home remedies"},
    "aurvedik nuskhe": {"canonical": "What is Ayurveda — Origin and Definition", "expansion": "ayurvedic home remedies herbs"},
    "gharelu nuskhe": {"canonical": "What is Ayurveda — Origin and Definition", "expansion": "ayurvedic home remedies herbs tulsi shunthi"},
    "triphla ke fayde": {"canonical": "Triphala — The Classical Three-Fruit Synergy", "expansion": "triphala benefits digestion bowels constipation"},
    "triphla ke fyde": {"canonical": "Triphala — The Classical Three-Fruit Synergy", "expansion": "triphala benefits digestion bowels constipation"},
    "prakruti kya hoti hai": {"canonical": "Prakriti and Vikriti — Individual Constitution vs Current Imbalance", "expansion": "prakriti constitution baseline doshas body type"},
    "vat pit kuf": {"canonical": "Tridosha Theory — Overview of the Three Bio-energies", "expansion": "vata pitta kapha tridosha balance"},
    "vaat pitt kaph": {"canonical": "Tridosha Theory — Overview of the Three Bio-energies", "expansion": "vata pitta kapha tridosha balance"},
    "vat pitta kapha": {"canonical": "Tridosha Theory — Overview of the Three Bio-energies", "expansion": "vata pitta kapha tridosha balance"},
    "three doshas": {"canonical": "Tridosha Theory — Overview of the Three Bio-energies", "expansion": "tridosha vata pitta kapha"},
    "3 doshas": {"canonical": "Tridosha Theory — Overview of the Three Bio-energies", "expansion": "tridosha vata pitta kapha"}
}

class QueryCorrectionResult:
    def __init__(
        self,
        original_query: str,
        normalized_query: str,
        canonical_terms: List[str],
        expansion_terms: List[str],
        corrections: Dict[str, str],
        display_interpretation: Optional[str] = None
    ):
        self.original_query = original_query
        self.normalized_query = normalized_query
        self.canonical_terms = canonical_terms
        self.expansion_terms = expansion_terms
        self.corrections = corrections
        self.display_interpretation = display_interpretation

class AyurvedaSpellingCorrector:
    """
    Intelligent Typo Corrector, Phonetic Matcher, and Intent Normalizer for Ayurveda & Health.
    Preserves stopwords and functional phrasing while identifying misspelled Ayurvedic entities.
    """

    def __init__(self):
        # Build comprehensive vocabulary of canonical patterns
        self.canonical_vocab: Set[str] = set()
        for term, data in CANONICAL_AYURVEDA_TERMS.items():
            self.canonical_vocab.add(term.lower())
            for pat in data.get("patterns", []):
                self.canonical_vocab.add(pat.lower())
            for syn in data.get("synonyms", []):
                self.canonical_vocab.add(syn.lower())

        # Also add all keys from exact typo map
        for k in EXACT_TYPO_MAP.keys():
            self.canonical_vocab.add(k.lower())

    def _normalize_phonetics(self, word: str) -> str:
        """Normalizes phonetic transliteration variations."""
        w = word.lower()
        w = re.sub(r"aa+", "a", w)
        w = re.sub(r"ee+", "i", w)
        w = re.sub(r"oo+", "u", w)
        w = re.sub(r"ph", "f", w)
        w = re.sub(r"w", "v", w)
        w = re.sub(r"sh", "s", w)
        w = re.sub(r"dh", "d", w)
        w = re.sub(r"th", "t", w)
        w = re.sub(r"kh", "k", w)
        w = re.sub(r"([a-z])\1+", r"\1", w)
        return w

    def correct_token(self, token: str) -> Tuple[str, bool]:
        """
        Corrects an individual token if it is a known typo or close match.
        Never alters preserved grammatical or question words.
        """
        t_clean = token.lower().strip("?,.!;:()\"'")
        if len(t_clean) <= 1 or t_clean in PRESERVED_WORDS:
            return token, False

        # 1. Exact match in typo map
        if t_clean in EXACT_TYPO_MAP:
            target = EXACT_TYPO_MAP[t_clean]
            return target, (t_clean != target)

        # 2. Exact match in canonical patterns
        for key, data in CANONICAL_AYURVEDA_TERMS.items():
            if t_clean in [p.lower() for p in data.get("patterns", [])]:
                return key, (t_clean != key)

        # 3. Phonetic skeleton matching (only if word >= 4 chars)
        if len(t_clean) >= 4:
            p_token = self._normalize_phonetics(t_clean)
            for cand in self.canonical_vocab:
                if len(cand) >= 4 and cand not in PRESERVED_WORDS:
                    if self._normalize_phonetics(cand) == p_token:
                        # Map cand to canonical term if possible
                        for key, data in CANONICAL_AYURVEDA_TERMS.items():
                            if cand in [p.lower() for p in data.get("patterns", [])] or cand == key:
                                return key, True
                        if cand in EXACT_TYPO_MAP:
                            return EXACT_TYPO_MAP[cand], True
                        return cand, True

        # 4. Difflib fuzzy match for longer words (>= 5 chars)
        if len(t_clean) >= 5:
            # Filter candidate pool so we only match against Ayurveda vocabulary, not common words
            candidates = [c for c in self.canonical_vocab if c not in PRESERVED_WORDS and len(c) >= 4]
            matches = difflib.get_close_matches(t_clean, candidates, n=1, cutoff=0.74)
            if matches:
                matched_cand = matches[0]
                for key, data in CANONICAL_AYURVEDA_TERMS.items():
                    if matched_cand in [p.lower() for p in data.get("patterns", [])] or matched_cand == key:
                        return key, True
                if matched_cand in EXACT_TYPO_MAP:
                    return EXACT_TYPO_MAP[matched_cand], True
                return matched_cand, True

        return token, False

    def process_query(self, query: str) -> QueryCorrectionResult:
        """
        Parses user query, corrects typos, extracts canonical entities and expansion terms.
        """
        q_lower = query.lower()
        corrections: Dict[str, str] = {}
        matched_canonical: List[str] = []
        extra_terms: List[str] = []

        # 1. Multi-word phrase matching
        for phrase, p_data in MULTI_WORD_PHRASES.items():
            if phrase in q_lower:
                canonical_title = p_data["canonical"]
                if canonical_title not in matched_canonical:
                    matched_canonical.append(canonical_title)
                extra_terms.extend(p_data["expansion"].split())

        # 2. Token-by-token correction
        tokens = query.split()
        normalized_tokens = []

        for token in tokens:
            match = re.match(r"^([^\w]*)([\w\-]+)([^\w]*)$", token, re.UNICODE)
            if match:
                prefix, core, suffix = match.groups()
                core_lower = core.lower()

                if core_lower in PRESERVED_WORDS:
                    normalized_tokens.append(token)
                    continue

                corrected_word, changed = self.correct_token(core)
                if changed:
                    corrections[core] = corrected_word
                    normalized_tokens.append(f"{prefix}{corrected_word}{suffix}")
                else:
                    normalized_tokens.append(token)

                # Match canonical data for the token or its corrected form
                lookup_word = corrected_word.lower()
                for key, data in CANONICAL_AYURVEDA_TERMS.items():
                    if lookup_word in [key] + [p.lower() for p in data.get("patterns", [])]:
                        if data["canonical"] not in matched_canonical:
                            matched_canonical.append(data["canonical"])
                        extra_terms.extend(data.get("keywords", []))
                        extra_terms.extend(data.get("synonyms", []))
            else:
                normalized_tokens.append(token)

        normalized_query_str = " ".join(normalized_tokens)

        # 3. Direct pattern sweep over normalized query string
        for key, data in CANONICAL_AYURVEDA_TERMS.items():
            for pat in data.get("patterns", []):
                if pat.lower() in q_lower or pat.lower() in normalized_query_str.lower():
                    if data["canonical"] not in matched_canonical:
                        matched_canonical.append(data["canonical"])
                    extra_terms.extend(data.get("keywords", []))

        # 4. Generate user-friendly interpretation display
        display_interpretation = None
        if corrections or matched_canonical:
            # Format clean titles
            clean_display_titles = []
            for t in matched_canonical:
                short_title = t.split(" — ")[0].split(" (")[0]
                if short_title not in clean_display_titles:
                    clean_display_titles.append(short_title)
            
            if clean_display_titles:
                display_interpretation = ", ".join(clean_display_titles[:3])
            elif corrections:
                display_interpretation = ", ".join(list(corrections.values())[:3])

        return QueryCorrectionResult(
            original_query=query,
            normalized_query=normalized_query_str,
            canonical_terms=matched_canonical,
            expansion_terms=list(dict.fromkeys(extra_terms)), # deduplicated preserving order
            corrections=corrections,
            display_interpretation=display_interpretation
        )

# Global spell corrector instance
spell_corrector = AyurvedaSpellingCorrector()
