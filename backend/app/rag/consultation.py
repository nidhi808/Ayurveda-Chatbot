"""
Ayurvedic Clinical Intake & Symptom Consultation Workflow (Rogi Pariksha & Prashna Pariksha).
Handles multi-turn symptom assessment, clarifying intake questions (duration, age, gender, medical history),
and structured recommendations with dosage timing (When and How to take / Sewan Vidhi & Anupana).
"""

import re
from typing import Dict, Any, Optional, Tuple, List

# Symptom categories and their keyword matchers
SYMPTOM_CATEGORIES = {
    "cough_cold": {
        "title": "Cough, Cold & Respiratory Distress (Kasa & Pratishyaya)",
        "title_lang": {
            "en": "Cough, Cold & Respiratory Distress (Kasa & Pratishyaya)",
            "hi": "खांसी, जुकाम एवं श्वसन विकार (कास एवं प्रतिश्याय)",
            "mr": "खोकला, सर्दी व श्वसन विकार (कास व प्रतिश्याय)"
        },
        "keywords": [
            r"\bcough\b", r"\bcold\b", r"\bkhansi\b", r"\bkhasi\b", r"\bkasi\b", r"\bkasa\b",
            r"\bsardi\b", r"\bzuka+m\b", r"\bjuka+m\b", r"\bbalgham\b", r"\bphlegm\b",
            r"\bmucus\b", r"\bsore\s+throat\b", r"\bgale\s+me\s+kharash\b", r"\bgale\s+me\s+dard\b",
            r"\bkhokla\b", r"\bpratishyaya\b", r"\bbronchitis\b", r"\brunny\s+nose\b", r"\bcongestion\b",
            r"\bsneeze\b", r"\bsneezing\b", r"\bcheenk\b", r"\bchest\s+congestion\b",
            r"खोकला", r"खोकल्या", r"खोकल्यासाठी", r"खांसी", r"खासी", r"कफ", r"सर्दी", r"जुकाम", r"बलगम", r"घसा"
        ],
        "default_herb": "tulsi",
        "specific_question": {
            "en": "Is your cough dry (Vataja) or accompanied by thick mucus/phlegm (Kaphaja)? Does it worsen at night or upon exposure to cold air?",
            "hi": "क्या आपकी खांसी सूखी है (Dry Cough) या कफ/बलगम वाली? क्या यह रात में या ठंडी हवा के संपर्क में आने पर ज्यादा बढ़ जाती है?",
            "mr": "तुमचा खोकला कोरडा आहे की कफयुक्त (बेडके पडणारा)? रात्री किंवा गारव्यात त्रास अधिक वाढतो का?"
        }
    },
    "digestive": {
        "title": "Digestive Imbalance & Acidity (Agnimandya & Amlapitta)",
        "title_lang": {
            "en": "Digestive Imbalance & Acidity (Agnimandya & Amlapitta)",
            "hi": "अम्लपित्त (एसिडिटी), गैस एवं पाचन विकार (अग्निमांद्य)",
            "mr": "ॲसिडिटी, गॅस व पचन विकार (अग्निमांद्य व आम्लपित्त)"
        },
        "keywords": [
            r"\bacidity\b", r"\bacid\s+reflux\b", r"\bheartburn\b", r"\bgas\b", r"\bbloating\b",
            r"\bindigestion\b", r"\bconstipation\b", r"\bkabz\b", r"\bkabja\b", r"\bpet\s+dard\b",
            r"\bpet\s+kharab\b", r"\bstomach\s+ache\b", r"\bstomach\s+pain\b", r"\bapachan\b",
            r"\bajeerna\b", r"\bamlapitta\b", r"\bvomiting\b", r"\bnausea\b", r"\bjalun\b",
            r"\bchhati\s+me\s+jalan\b", r"\bkhatti\s+dakar\b", r"\bpet\s+saaf\s+nahi\b",
            r"गॅस", r"ॲसिडिटी", r"पोटदुखी", r"अम्लपित्त", r"अपचन", r"कब्ज", r"जलन", r"खट्टी", r"डकार", r"जळजळ", r"मळमळ", r"एसिडिटी"
        ],
        "default_herb": "triphala",
        "specific_question": {
            "en": "Do you feel burning in your chest/throat (Pitta), severe gas/bloating (Vata), or heaviness and lack of appetite after meals (Kapha/Ama)?",
            "hi": "क्या आपको छाती/गले में जलन व खट्टी डकारें (पित्त), पेट में गैस व भारीपन (वात), या भोजन के बाद भूख न लगना और सुस्ती (कफ/आम) महसूस होती है?",
            "mr": "तुम्हाला छातीत किंवा घशात जळजळ (पित्त), पोट फुगणे व गॅस (वात), की जेवणानंतर पोट जड पडणे व भूक मंदावणे (कफ/आम) असा त्रास आहे?"
        }
    },
    "joint_pain": {
        "title": "Joint Pain, Stiffness & Arthritis (Sandhivata & Amavata)",
        "title_lang": {
            "en": "Joint Pain, Stiffness & Arthritis (Sandhivata & Amavata)",
            "hi": "जोड़ों का दर्द, गठिया एवं जकड़न (संधिवात एवं आमवात)",
            "mr": "सांधेदुखी, संधिवात व कडकपणा (संधिवात व आमवात)"
        },
        "keywords": [
            r"\bjoint\s+pain\b", r"\bknee\s+pain\b", r"\barthritis\b", r"\bsandhivata\b",
            r"\bamavata\b", r"\bgathiya\b", r"\bghutno\s+me\s+dard\b", r"\bback\s+pain\b",
            r"\bkamar\s+dard\b", r"\bstiffness\b", r"\bbody\s+ache\b", r"\bbadan\s+dard\b",
            r"\bswelling\s+in\s+joints\b", r"\bsandhi\s+shula\b", r"\bjoint\s+stiffness\b",
            r"गुडघ्यात", r"गुडघेदुखी", r"सांधेदुखी", r"कडकपणा", r"कंबरदुखी", r"पाठदुखी", r"जोड़ों", r"गठिया", r"जकड़न", r"संधिवात", r"आमवात", r"वेदना"
        ],
        "default_herb": "ashwagandha",
        "specific_question": {
            "en": "Do your joints have morning stiffness and swelling that improves as you move around (Amavata), or is it sharp clicking pain that worsens with movement and cold (Sandhivata)?",
            "hi": "क्या सुबह उठने पर जोड़ों में तेज जकड़न व सूजन होती है जो दिन में चलने-फिरने से कम होती है, या चलने पर तेज दर्द और जोड़ों से कट-कट की आवाज आती है?",
            "mr": "सकाळी उठल्यावर सांध्यांमध्ये कडकपणा व सूज असते का, की हालचाल करताना सांध्यांमध्ये तीव्र वेदना होतात?"
        }
    },
    "stress_sleep": {
        "title": "Stress, Anxiety & Insomnia (Anidra & Manovaha Vikara)",
        "title_lang": {
            "en": "Stress, Anxiety & Insomnia (Anidra & Manovaha Vikara)",
            "hi": "तनाव, चिंता एवं अनिद्रा (नींद न आना)",
            "mr": "तणाव, चिंता व निद्रानाश (शांत झोप न लागणे)"
        },
        "keywords": [
            r"\binsomnia\b", r"\bsleep\b", r"\bsleeplessness\b", r"\bneend\s+nahi\s+aati\b",
            r"\bneend\s+na\s+aana\b", r"\banidra\b", r"\bstress\b", r"\banxiety\b",
            r"\btanav\b", r"\bchinta\b", r"\brestless\b", r"\bfatigue\b", r"\bexhaustion\b",
            r"\bthakan\b", r"\bsir\s+bhari\b", r"\bmental\s+stress\b",
            r"झोप", r"निद्रानाश", r"तणाव", r"चिंता", r"नींद", r"अनिद्रा", r"थकवा", r"थकान"
        ],
        "default_herb": "ashwagandha",
        "specific_question": {
            "en": "Do you struggle to fall asleep due to racing thoughts (Vata), wake up in the middle of the night feeling warm/irritable (Pitta), or feel sluggish and exhausted despite sleeping (Kapha)?",
            "hi": "क्या आपको अत्यधिक विचारों के कारण नींद आने में परेशानी होती है (वात), रात में अचानक नींद खुल जाती है (पित्त), या दिनभर सुस्ती और थकान बनी रहती है?",
            "mr": "सततच्या विचारांमुळे झोप लागत नाही का, की रात्री मध्यंतरी जाग येते आणि सकाळी थकवा जाणवतो?"
        }
    },
    "skin_hair": {
        "title": "Skin Allergies & Hair Issues (Twak Roga & Khalitya)",
        "title_lang": {
            "en": "Skin Allergies & Hair Issues (Twak Roga & Khalitya)",
            "hi": "त्वचा रोग, एलर्जी, कील-मुहांसे एवं बाल झड़ना (खालित्य)",
            "mr": "त्वचा रोग, ॲलर्जी व केस गळती (खालित्य)"
        },
        "keywords": [
            r"\bacne\b", r"\bpimples\b", r"\bskin\s+rash\b", r"\bitching\b", r"\bkhujli\b",
            r"\beczema\b", r"\btwak\s+roga\b", r"\bhair\s+fall\b", r"\bhair\s+loss\b",
            r"\bbaal\s+jhadna\b", r"\bdandruff\b", r"\broosi\b", r"\bkeshadourbalya\b",
            r"\bskin\s+allergy\b", r"\bboils\b", r"\bfode\s+funsi\b",
            r"त्वचा", r"खाज", r"केस गळती", r"केस गळणे", r"कोंडा", r"मुंहासे", r"खुजली", r"रूसी"
        ],
        "default_herb": "neem",
        "specific_question": {
            "en": "Is the skin red, burning, and prone to oily breakouts (Pitta), or is it excessively dry, scaly, and itchy (Vata/Kapha)?",
            "hi": "क्या त्वचा पर लालिमा, जलन और दाने हैं (पित्त), या त्वचा अत्यधिक सूखी, पपड़ीदार और खुजली वाली है (वात/कफ)?",
            "mr": "त्वचेवर लालसरपणा, खाज व जळजळ आहे का, की त्वचा कोरडी व भेगा पडलेली आहे?"
        }
    },
    "general_symptom": {
        "title": "General Health Imbalance & Discomfort",
        "title_lang": {
            "en": "General Health Imbalance & Discomfort",
            "hi": "शारीरिक अस्वस्थता एवं स्वास्थ्य विकार",
            "mr": "शारीरिक अस्वस्थता व आरोग्य समस्या"
        },
        "keywords": [
            r"\bsymptom\b", r"\bsymptoms\b", r"\bdisease\b", r"\billness\b", r"\bbeemari\b",
            r"\bbimari\b", r"\btakleef\b", r"\bparesha+ni\b", r"\btras\b", r"\bproblem\b",
            r"\bsuffering\s+from\b", r"\bi\s+have\s+\w+\b", r"\bfeeling\s+unwell\b",
            r"त्रास", r"आजार", r"अस्वस्थ", r"बीमारी", r"तकलीफ", r"परेशानी"
        ],
        "default_herb": "tulsi",
        "specific_question": {
            "en": "What specific bodily changes or triggers have you noticed (e.g., related to weather, specific foods, or time of day)?",
            "hi": "आपने विशेष रूप से क्या बदलाव या ट्रिगर्स महसूस किए हैं (जैसे मौसम में बदलाव, विशेष भोजन या दिन/रात के समय)?",
            "mr": "तुम्हाला विशेषतः कोणत्या वेळी किंवा कारणाने हा त्रास अधिक जाणवतो (उदा. विशिष्ट अन्न, हवामानातील बदल)?"
        }
    }

}


class AyurvedicConsultationEngine:
    """Manages Ayurvedic Rogi Pariksha intake questioning and symptom protocol generation."""

    @classmethod
    def detect_symptom_intent(cls, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Detects whether user query describes a symptom or health complaint."""
        q = query.lower().strip()

        # Check explicit emergency keywords first (let safety classifier handle acute emergencies)
        if any(w in q for w in ["heart attack", "stroke", "unconscious", "poisoning", "suicide"]):
            return None

        for cat_key, info in SYMPTOM_CATEGORIES.items():
            for pat in info["keywords"]:
                if re.search(pat, q):
                    return cat_key, info
        return None

    @classmethod
    def extract_intake_data(cls, query: str, conversation_context: str = "") -> Dict[str, Any]:
        """
        Extracts intake attributes (Duration, Age, Gender, Conditions, Specifics)
        from current query and prior user utterances.
        """
        user_utterances = [query.strip().lower()]
        for line in conversation_context.splitlines():
            line_str = line.strip()
            if line_str.lower().startswith("user:"):
                user_utterances.append(line_str[5:].strip().lower())

        combined = " \n ".join(user_utterances)

        data: Dict[str, Any] = {
            "duration": None,
            "age": None,
            "gender": None,
            "conditions": None,
            "specifics": None
        }

        # 1. Extract Duration (English, Roman Hindi, Devanagari Hindi/Marathi)
        dur_patterns = [
            r"\b(\d+|one|two|three|four|five|several|few)\s*(?:days?|weeks?|months?|d|w|m)\b",
            r"\b(\d+|ek|do|teen|char|kuch)\s*(?:din|hafte|mahine)\b",
            r"\b(\d+)\s*(?:दिन|दिवस|महिने|हफ्ते|आठवडे)\b",
            r"\b(?:since|from)\s+(?:yesterday|last\s+\w+|\d+\s+\w+)\b",
            r"\b(?:kal|parso|काल|परवा)\s*(?:se|पासून)?\b",
        ]
        for dp in dur_patterns:
            m = re.search(dp, combined)
            if m:
                data["duration"] = m.group(0).strip()
                break

        # 2. Extract Age
        age_patterns = [
            r"(?:age|umar|vaya|उम्र|वय)\s*[:=]?\s*(\d{1,2})\b",
            r"\b(\d{1,2})\s*(?:years?\s+old|saal|yo|yr|yrs|varsh|साल|वर्ष|वर्षे)\b",
            r"\b(\d{1,2})\s*(?:m|f|male|female|purush|mahila|पुरुष|महिला)\b"
        ]
        for ap in age_patterns:
            m = re.search(ap, combined)
            if m:
                data["age"] = m.group(1).strip()
                break

        # 3. Extract Gender
        gen_match = re.search(r"\b(male|female|purush|mahila|man|woman|boy|girl|stree|पुरुष|महिला|स्त्री)\b", combined)
        if gen_match:
            g = gen_match.group(1)
            if g in ["male", "purush", "man", "boy", "पुरुष"]:
                data["gender"] = "Male"
            else:
                data["gender"] = "Female"

        # 4. Extract Existing Chronic Conditions / Medical History
        no_cond = re.search(
            r"(no\s+(?:other\s+)?(?:disease|illness|issues?)|no|none|nahi|nahin|kuch\s+nahi|nhi|नहीं|नाही|काही\s+नाही|कोणताही\s+नाही|कोई\s+अन्य\s+बीमारी\s+नहीं|अन्य\s+कोई\s+बीमारी\s+नहीं)",
            combined
        )
        if no_cond:
            data["conditions"] = "None reported"
        else:
            found_conds = []
            if re.search(r"\b(diabetes|sugar|prameha|मधुमेह|शुगर)\b", combined):
                found_conds.append("Diabetes")
            if re.search(r"\b(bp|blood\s+pressure|hypertension|रक्तदाब|बीपी)\b", combined):
                found_conds.append("Hypertension")
            if re.search(r"\b(thyroid|थायरॉइड|थायरॉईड)\b", combined):
                found_conds.append("Thyroid")
            if re.search(r"\b(asthma|dama|दमा|अस्थमा)\b", combined):
                found_conds.append("Asthma")
            if re.search(r"\b(pregnant|pregnancy|गर्भवती|गर्भावस्थेत)\b", combined):
                found_conds.append("Pregnancy")
            if found_conds:
                data["conditions"] = ", ".join(found_conds)

        # 5. Extract Symptom Specifics
        spec_list = []
        if re.search(r"\b(dry|sookhi|sukhi|korada|सूखी|कोरडा)\b", combined):
            spec_list.append("Dry / Vataja")
        if re.search(r"\b(phlegm|balgham|mucus|kaph|wet|कफ|बलगम|बेडके)\b", combined):
            spec_list.append("Productive / Kaphaja")
        if re.search(r"\b(burning|jalan|acidity|sour|khatta|जलन|गैस|खट्टी|आंबट|जळजळ)\b", combined):
            spec_list.append("Burning / Pittaja")
        if re.search(r"\b(stiffness|swelling|jakad|sujan|जकड़न|सूजन|कडकपणा|सूज)\b", combined):
            spec_list.append("Stiffness / Swelling")
        if re.search(r"\b(night|raat|morning|subah|रात|सकाळी|रात्री)\b", combined):
            spec_list.append("Time-aggravated")
        if spec_list:
            data["specifics"] = ", ".join(spec_list)

        return data


    @classmethod
    def is_intake_complete(cls, intake_data: Dict[str, Any]) -> bool:
        """
        Determines whether sufficient intake data has been collected
        to generate a tailored protocol.
        A complete intake requires:
        1. Demographics (Age or Gender) AND Clinical context (Duration, Specifics, or Medical History)
        OR
        2. At least 3 distinct clinical dimensions answered.
        """
        has_demographic = bool(intake_data.get("age") or intake_data.get("gender"))
        has_duration = bool(intake_data.get("duration"))
        has_conditions = bool(intake_data.get("conditions"))
        has_specifics = bool(intake_data.get("specifics"))

        clinical_points = sum([has_duration, has_conditions, has_specifics])

        if has_demographic and clinical_points >= 1:
            return True

        if clinical_points >= 3:
            return True

        return False


    @classmethod
    def generate_intake_questions(
        cls,
        cat_key: str,
        cat_info: Dict[str, Any],
        user_query: str,
        lang: str = "en"
    ) -> Tuple[str, List[str]]:
        """
        Asks clarifying Rogi Pariksha intake questions before prescribing herbs,
        tailored to the user's specific symptom.
        """
        spec_q = cat_info["specific_question"].get(lang, cat_info["specific_question"]["en"])
        title = cat_info.get("title_lang", {}).get(lang, cat_info.get("title", "Health Imbalance"))

        if lang == "mr":
            answer = (
                f"### 🌿 आयुर्वेदिक सल्लामसलत व रोगी परीक्षा (Rogi Pariksha)\n\n"
                f"मला समजले की तुम्हाला **{title}** चा त्रास होत आहे. आयुर्वेदात (*चरक संहिता*) प्रत्येक व्यक्तीची प्रकृती "
                f"आणि दोषांचे असंतुलन वेगळे असते. तुमच्या प्रकृतीनुसार सर्वात योग्य औषधी वनस्पती, घेण्याची पद्धत (अनुपान) "
                f"आणि योग्य वेळ (Timing) निश्चित करण्यासाठी कृपया खालील ४ महत्त्वाच्या प्रश्नांची उत्तरे द्या:\n\n"
                f"1. ⏳ **कालावधी (Duration)**: हा त्रास तुम्हाला नेमका किती दिवसांपासून किंवा आठवड्यांपासून आहे?\n"
                f"2. 👤 **वय आणि लिंग (Age & Gender)**: तुमचे वय आणि लिंग काय आहे?\n"
                f"3. 🩺 **वैद्यकीय इतिहास (Medical History)**: तुम्हाला रक्तदाब (BP), मधुमेह (Sugar), ॲसिडिटी, थायरॉईड असा कोणताही जुना आजार आहे का किंवा इतर औषधे सुरू आहेत का?\n"
                f"4. 🔍 **लक्षणे (Symptom Details)**: {spec_q}\n\n"
                f"---\n"
                f"💡 *तुम्ही थेट अशा प्रकारे उत्तर देऊ शकता: 'वय २८, पुरुष, ३ दिवस, कोरडा खोकला, इतर कोणताही आजार नाही'* किंवा उपलब्ध माहिती सांगा."
            )
            followups = [
                "वय २८, पुरुष, ३ दिवस, कोरडा खोकला, इतर आजार नाही",
                "वय ४५, महिला, १ आठवडा, कफयुक्त, बीपीचा त्रास आहे",
                "वय ३२, पुरुष, ५ दिवस, जळजळ व गॅस, कोणताही आजार नाही"
            ]
        elif lang == "hi":
            answer = (
                f"### 🌿 आयुर्वेदिक परामर्श एवं रोगी परीक्षा (Rogi Pariksha)\n\n"
                f"मैं समझ सकता हूँ कि आप **{title}** से परेशान हैं। शास्त्रीय आयुर्वेद (*चरक संहिता*) के अनुसार, "
                f"प्रत्येक व्यक्ति की प्रकृति (वात, पित्त, कफ) भिन्न होती है। आपके लिए सबसे उपयुक्त शास्त्रीय जड़ी-बूटी, "
                f"सेवन विधि (अनुपान जैसे शहद/दूध/कोमट जल) और समय (Timing) के सही निर्धारण के लिए कृपया नीचे दिए गए ४ सवालों के संक्षिप्त उत्तर दें:\n\n"
                f"1. ⏳ **अवधि (Duration)**: आपको यह समस्या कितने दिनों या हफ्तों से है?\n"
                f"2. 👤 **आयु एवं लिंग (Age & Gender)**: आपकी उम्र और लिंग क्या है?\n"
                f"3. 🩺 **पूर्व इतिहास (Medical History)**: क्या आपको ब्लड प्रेशर (BP), शुगर (Diabetes), थायरॉइड, या अन्य कोई पुरानी बीमारी है या कोई नियमित दवा चल रही है?\n"
                f"4. 🔍 **लक्षणों की प्रकृति (Symptom Nature)**: {spec_q}\n\n"
                f"---\n"
                f"💡 *आप सीधे इस प्रारूप में जवाब दे सकते हैं: 'उम्र 28, पुरुष, 3 दिन से, सूखी खांसी, कोई अन्य बीमारी नहीं'*"
            )
            followups = [
                "उम्र 28, पुरुष, 3 दिन से, सूखी खांसी, कोई बीमारी नहीं",
                "उम्र 42, महिला, 1 हफ्ते से, कफ/बलगम, बीपी की दवा चलती है",
                "उम्र 35, पुरुष, 4 दिन से, सीने में जलन और गैस, कोई बीमारी नहीं"
            ]
        else:
            answer = (
                f"### 🌿 Ayurvedic Consultation & Rogi Pariksha (Patient Intake)\n\n"
                f"I understand you are experiencing symptoms related to **{title}**. In classical Ayurveda (*Charaka Samhita*), "
                f"treatments are strictly personalized to your constitution (**Prakriti**) and current doshic imbalance (**Vikriti**). \n\n"
                f"Before recommending specific herbs, anupana (carrier vehicles), and timing, please answer these 4 quick intake questions:\n\n"
                f"1. ⏳ **Duration**: For how many days or weeks have you been experiencing this symptom?\n"
                f"2. 👤 **Age & Gender**: What is your age and gender?\n"
                f"3. 🩺 **Medical History**: Do you have any chronic conditions (e.g., High BP, Diabetes, Acidity, Thyroid, or Pregnancy) or ongoing prescription medications?\n"
                f"4. 🔍 **Symptom Nature**: {spec_q}\n\n"
                f"---\n"
                f"💡 *Tip: You can simply reply in this format: 'Age 28, Male, 3 days, dry cough, no other illness'*."
            )
            followups = [
                "Age 28, Male, 3 days, dry cough, no other illness",
                "Age 45, Female, 1 week, with phlegm, have high BP",
                "Age 32, Male, 4 days, burning sensation & acidity, no other illness"
            ]

        return answer, followups

    @classmethod
    def generate_tailored_protocol(
        cls,
        cat_key: str,
        intake_data: Dict[str, Any],
        citations: List[Any],
        lang: str = "en"
    ) -> str:
        """
        Generates the customized Ayurvedic prescription protocol,
        including which herbs to take, when, and how to take them.
        """
        dur = intake_data.get("duration") or "A few days"
        age = intake_data.get("age") or "Adult"
        gen = intake_data.get("gender") or "Not specified"
        cond = intake_data.get("conditions") or "None reported"
        spec = intake_data.get("specifics") or "Standard presentation"

        if cat_key == "cough_cold":
            if "Dry" in spec or "dry" in str(spec).lower():
                herb_primary = "Sitopaladi Churna + Yashtimadhu (Mulethi)"
                dosha_desc = "Vata-Kaphaja Kasa (Dry, irritated bronchial pathways with throat tickle)"
                timing_morning = "1/2 teaspoon (approx 2g) Sitopaladi Churna mixed with 1 teaspoon pure honey, 20 mins after breakfast."
                timing_night = "Warm infusion of Mulethi (Licorice) and Tulsi leaves with a pinch of black pepper (Pippali) before bedtime."
                anupana = "Pure raw Honey (Madhu) or Lukewarm Water (Ushnodaka). Note: Never boil honey."
                pathya = "Warm vegetable soups, steamed food, hot ginger-tulsi tea, honey, warm water sips."
                apathya = "Cold refrigerated drinks, ice cream, curd (especially at night), bananas, oily deep-fried foods."
            else:
                herb_primary = "Tulsi (Holy Basil) + Sitopaladi Churna + Trikatu"
                dosha_desc = "Kaphaja Kasa (Excess mucus accumulation and sluggish chest congestion)"
                timing_morning = "1/2 teaspoon Sitopaladi Churna with 1/4 teaspoon Trikatu and honey twice daily after meals."
                timing_night = "Steam inhalation (Swedana) with Tulsi leaves / Ajwain, followed by warm water."
                anupana = "Lukewarm water or honey."
                pathya = "Warm light foods, barley soup, roasted garlic, black pepper, clove, warm water."
                apathya = "Dairy products, curd, cold drinks, sweets, day sleep (Diva-swapna)."

        elif cat_key == "digestive":
            herb_primary = "Triphala Churna + Yashtimadhu / Avipattikar"
            dosha_desc = "Pitta-Vata imbalance with Agnimandya (Weak digestive fire) and Ama accumulation"
            timing_morning = "Yashtimadhu tea or Coriander-Cumin-Fennel (CCF) water on an empty stomach."
            timing_night = "1 teaspoon (approx 3-5g) Triphala Churna with lukewarm water 30 minutes before sleep."
            anupana = "Lukewarm water (Ushnodaka) or Cow's Ghee (for burning acidity)."
            pathya = "Fresh pomegranate, sweet fruits, moong dal khichdi, boiled warm water, buttermilk with roasted jeera."
            apathya = "Extreme chilies, excessively sour/fermented foods, fried items, late-night dinners, sleeping immediately after meals."

        elif cat_key == "joint_pain":
            herb_primary = "Ashwagandha (Withania somnifera) + Haridra (Turmeric) + Guggulu"
            dosha_desc = "Vata Prakopa in Asthi and Sandhi (Bones and joints) with possible Ama stiffness"
            timing_morning = "1/2 teaspoon Ashwagandha root powder boiled in warm milk/water after breakfast."
            timing_night = "Golden Milk: Warm milk with 1/2 teaspoon Haridra (Turmeric) and a pinch of black pepper before bed."
            anupana = "Warm Cow's Milk or Warm Water."
            pathya = "Warm freshly cooked foods, sesame seeds, garlic, ginger, gentle oil massage (Abhyanga with sesame oil)."
            apathya = "Cold water baths, dry/raw cold salads, chickpeas, rajma, exposure to cold AC drafts."

        elif cat_key == "stress_sleep":
            herb_primary = "Ashwagandha + Brahmi (Bacopa monnieri) + Chamomile"
            dosha_desc = "Vata-Pitta disturbance in Manovaha Srotas (Mental channels causing restless sleep)"
            timing_morning = "1/2 teaspoon Brahmi powder or Ashwagandha after breakfast with warm water."
            timing_night = "1/2 teaspoon Ashwagandha powder with a warm cup of milk and a pinch of nutmeg (Jaiphal) 45 mins before sleep."
            anupana = "Warm Cow's Milk (Ksira) or warm water."
            pathya = "Warm meals, applying warm sesame oil/ghee to the soles of feet (Padabhyanga), regular bedtime routine."
            apathya = "Caffeine after 4 PM, excessive screen time before bed, late-night heavy meals, skipping dinner."

        elif cat_key == "skin_hair":
            herb_primary = "Neem (Azadirachta indica) + Haridra (Turmeric) + Amla"
            dosha_desc = "Rakta and Pitta Dushti (Blood and fire element aggravation manifesting on skin/scalp)"
            timing_morning = "Neem leaves juice or 1-2 Neem capsules on an empty stomach with warm water."
            timing_night = "1/2 teaspoon Amla powder mixed with warm water after dinner."
            anupana = "Lukewarm water or Aloe Vera juice."
            pathya = "Bitter vegetables (karela, methi), fresh amla, cucumber, plenty of clean warm water."
            apathya = "Excessively oily, spicy, junk foods, excessive sun exposure, harsh chemical cosmetics."

        else:
            herb_primary = "Tulsi + Guduchi (Giloy) + Amalaki"
            dosha_desc = "Tridoshic imbalance with weakened Ojas (Vital immunity)"
            timing_morning = "Guduchi / Giloy kwath (decoction) or Tulsi tea with a drop of honey."
            timing_night = "1/2 teaspoon Amla powder with warm water."
            anupana = "Lukewarm water."
            pathya = "Easily digestible light home-cooked food, fresh fruits, warm water."
            apathya = "Stale food, deep-fried items, cold beverages."

        if lang == "mr":
            return (
                f"### 🌿 वैयक्तिकृत आयुर्वेदिक उपचार व दिनचर्या (Customized Protocol)\n\n"
                f"तुमच्या दिलेल्या माहितीनुसार (**वय: {age}, लिंग: {gen}, कालावधी: {dur}, लक्षणे: {spec}, पूर्व आजार: {cond}**), "
                f"खालीलप्रमाणे शास्त्रीय आयुर्वेदिक मार्गदर्शन खालीलप्रमाणे आहे:\n\n"
                f"#### 1. 🔍 आयुर्वेदिक निदान व दोष असंतुलन (Doshic Assessment):\n"
                f"• **दोष प्रकोपाची स्थिती**: {dosha_desc}.\n"
                f"• **अग्नी व आम**: पचनशक्ती (अग्नी) मंदावल्यामुळे शरिरात 'आम' (टॉक्सिन्स) साठल्याची शक्यता आहे.\n\n"
                f"#### 2. 🍵 शिफारस केलेल्या शास्त्रीय औषधी वनस्पती (Recommended Herbs):\n"
                f"• **मुख्य औषध**: **{herb_primary}**\n"
                f"• **शास्त्रीय संदर्भ**: आयुर्वेदिक फॉर्म्युलेरी ऑफ इंडिया (AFI) आणि चरक संहिता.\n\n"
                f"#### 3. ⏰ केव्हा आणि कसे घ्यावे (Sewan Vidhi & Anupana - When and How to Take):\n"
                f"• 🌅 **सकाळी (Morning)**: {timing_morning}\n"
                f"• 🌇 **रात्री (Night/Bedtime)**: {timing_night}\n"
                f"• 🍯 **अनुपान (माध्यम)**: {anupana}\n\n"
                f"#### 4. 🥗 आहार व जीवनशैली नियम (पथ्य व अपथ्य):\n"
                f"• ✅ **पथ्य (काय खावे / करावे)**: {pathya}\n"
                f"• ❌ **अपथ्य (काय टाळावे)**: {apathya}\n\n"
                f"#### ⚠️ महत्त्वाची वैद्यकीय सूचना:\n"
                f"हा सल्ला पारंपरिक आयुर्वेदिक तत्त्वांवर आधारित शैक्षणिक मार्गदर्शनासाठी आहे. जर लक्षणे ५-७ दिवसांपेक्षा जास्त काळ टिकून राहिली "
                f"किंवा तीव्र त्रास होत असल्यास कृपया त्वरित नोंदणीकृत आयुर्वेदिक वैद्यांचा प्रत्यक्ष सल्ला घ्या."
            )
        elif lang == "hi":
            return (
                f"### 🌿 वैयक्तिक आयुर्वेदिक परामर्श व सेवन विधि (Personalized Protocol)\n\n"
                f"आपके द्वारा दी गई जानकारी (**उम्र: {age}, लिंग: {gen}, अवधि: {dur}, लक्षणों का प्रकार: {spec}, पूर्व इतिहास: {cond}**) "
                f"के आधार पर शास्त्रीय आयुर्वेदिक निदान एवं उपचार प्रोटोकॉल निम्नलिखित है:\n\n"
                f"#### 1. 🔍 आयुर्वेदिक दोष विश्लेषण (Ayurvedic Doshic Assessment):\n"
                f"• **दोष असंतुलन**: {dosha_desc}।\n"
                f"• **अग्नि एवं आम स्थिति**: जठराग्नि के मंद होने से शरीर के स्रोतों में अवरोध उत्पन्न हो सकता है।\n\n"
                f"#### 2. 🍵 उपयुक्त आयुर्वेदिक औषधियां एवं योग (Recommended Herbs):\n"
                f"• **प्रमुख शास्त्रीय योग**: **{herb_primary}**\n"
                f"• **शास्त्रीय आधार**: आयुर्वेदिक फार्माकोपिया ऑफ इंडिया (API) व चरक संहिता।\n\n"
                f"#### 3. ⏰ कब और कैसे सेवन करें (Sewan Vidhi & Anupana - When and How to Take):\n"
                f"• 🌅 **प्रातःकाल (सुबह)**: {timing_morning}\n"
                f"• 🌇 **सायंकाल / रात्रि (सोने से पहले)**: {timing_night}\n"
                f"• 🍯 **अनुपान (किसके साथ लें)**: {anupana}\n\n"
                f"#### 4. 🥗 खान-पान और दिनचर्या नियम (पथ्य एवं अपथ्य):\n"
                f"• ✅ **पथ्य (क्या खाएं / अनुकूल)**: {pathya}।\n"
                f"• ❌ **अपथ्य (क्या न खाएं / हानिकारक)**: {apathya}।\n\n"
                f"#### ⚠️ चिकित्सीय सावधानी एवं परामर्श:\n"
                f"यह जानकारी पारंपरिक आयुर्वेदिक सिद्धांतों पर आधारित शैक्षिक मार्गदर्शन है। यदि समस्या ५-७ दिनों से अधिक समय तक बनी रहती है "
                f"या तीव्रता बढ़ती है, तो कृपया तुरंत किसी योग्य आयुर्वेदिक वैद्य या चिकित्सक से व्यक्तिगत परामर्श लें।"
            )
        else:
            return (
                f"### 🌿 Personalized Ayurvedic Guidance Protocol (Rogi Pariksha Assessment)\n\n"
                f"Based on your profile (**Age: {age}, Gender: {gen}, Duration: {dur}, Symptom Type: {spec}, History: {cond}**), "
                f"here is the classical Ayurvedic management protocol:\n\n"
                f"#### 1. 🔍 Ayurvedic Assessment & Doshic Analysis:\n"
                f"• **Doshic Imbalance**: {dosha_desc}.\n"
                f"• **Digestive Fire (Agni)**: Mandagni (sluggish digestive fire) may be contributing to Ama (metabolic toxins).\n\n"
                f"#### 2. 🍵 Classical Ayurvedic Herbs & Formulations:\n"
                f"• **Primary Formulations**: **{herb_primary}**\n"
                f"• **Classical Authority**: Ayurvedic Pharmacopoeia of India (API) & Charaka Samhita.\n\n"
                f"#### 3. ⏰ When and How to Take (Administration Schedule & Anupana):\n"
                f"• 🌅 **Morning (After Breakfast)**: {timing_morning}\n"
                f"• 🌇 **Night (Bedtime)**: {timing_night}\n"
                f"• 🍯 **Anupana (Carrier Vehicle)**: {anupana}\n\n"
                f"#### 4. 🥗 Dietary & Lifestyle Rules (Pathya & Apathya):\n"
                f"• ✅ **Pathya (Foods & habits to favor)**: {pathya}\n"
                f"• ❌ **Apathya (Foods & habits to strictly avoid)**: {apathya}\n\n"
                f"#### ⚠️ Clinical Disclaimer:\n"
                f"This protocol is provided for educational and traditional health-literacy purposes. If symptoms persist beyond 5-7 days or worsen, "
                f"please consult a licensed Ayurvedic Vaidya or certified physician for an in-person clinical examination."
            )
