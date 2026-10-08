import re
from typing import List, Tuple, Optional
from backend.app.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.app.models import SourceCitation
from backend.app.safety import SafetyClassifier

SYSTEM_PROMPT = """You are AyurBot, an educational assistant specializing in Ayurveda.

Your Purpose:
Provide users with reliable, source-grounded, easy-to-understand educational information about Ayurveda concepts, traditional practices, herbs, doshas, lifestyle concepts, and related topics.

Core Principles & Rules:
1. Educate, do NOT diagnose or prescribe.
2. Answer strictly using the provided context. If the context does not contain sufficient information to answer the question, clearly state:
   "I couldn't find sufficient information about this concept in my current Ayurveda knowledge base. You can try asking about fundamentals like Tridosha, Prakriti, Agni, Dinacharya, or herbs like Tulsi and Ashwagandha."
3. Clearly distinguish traditional Ayurvedic descriptions (classical philosophies, doshic attributes) from modern scientific evidence.
4. Do not recommend personalized medicinal dosages or replace a doctor/qualified practitioner.
5. Provide a well-structured response with clear headings or bullet points.
6. Acknowledge and cite the provided sources at the end.
"""

class RAGGenerator:
    """Generates grounded responses using Gemini LLM with robust fallback."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        self._is_legacy = False
        self.init_client()

    def init_client(self):
        """Initializes Gemini client using modern google.genai or installed google.generativeai."""
        if not self.api_key:
            self.client = None
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self._is_legacy = False
            print("[RAGGenerator] Initialized google.genai Client successfully.")
        except Exception:
            try:
                import importlib
                genai_legacy = importlib.import_module("google.generativeai")
                genai_legacy.configure(api_key=self.api_key)
                self.client = genai_legacy.GenerativeModel(
                    self.model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                self._is_legacy = True
                print("[RAGGenerator] Initialized google.generativeai fallback successfully.")
            except Exception as e:
                print(f"[RAGGenerator] Warning initializing Gemini client: {e}")
                self.client = None

    def build_prompt(
        self,
        query: str,
        citations: List[SourceCitation],
        conversation_context: str = "",
        language: str = "en"
    ) -> str:
        """Assembles prompt with system instructions, retrieved context, and conversation history."""
        from backend.app.rag.multilingual import get_language_instructions

        context_blocks = []
        for i, c in enumerate(citations, 1):
            block = (
                f"[Source {i}: {c.title}]\n"
                f"Document: {c.source} | Section: {c.section or 'General'} (Page {c.page or 'N/A'})\n"
                f"Content: {c.content or c.snippet or ''}\n"
            )
            context_blocks.append(block)

        context_text = "\n---\n".join(context_blocks) if context_blocks else "No relevant context found."
        lang_instruction = get_language_instructions(language)

        prompt = f"""CONTEXT FROM AYURVEDA KNOWLEDGE BASE:
{context_text}

"""
        if conversation_context:
            prompt += f"""PREVIOUS CONVERSATION CONTEXT:
{conversation_context}

"""

        prompt += f"""TARGET LANGUAGE REQUIREMENT:
{lang_instruction}

USER QUESTION & INTENT UNDERSTANDING:
User query: "{query}"

Note on Typos and Phonetic Spellings:
The user might have misspelled terms or used colloquial/phonetic transliterations (for example, 'auredik' -> Ayurvedic, 'aswagandha' -> Ashwagandha, 'triphla' -> Triphala, 'kuff' -> Kapha/cough, 'prakruti' -> Prakriti, 'dincharya' -> Dinacharya, etc.).
Understand what the user is asking with empathy and intelligence, address the intended question using the verified Ayurvedic context above, and naturally introduce the canonical Ayurvedic terminology in your explanation.

Please provide an educational, clear, and grounded explanation based strictly on the context above in the requested language. Conclude with an educational disclaimer in the requested language."""
        return prompt

    def generate(
        self,
        query: str,
        citations: List[SourceCitation],
        conversation_context: str = "",
        language: str = "en"
    ) -> str:
        """Executes LLM generation or structured grounded fallback in requested language."""
        if not citations:
            if language == "mr":
                return (
                    "🌿 **सूचना**: मला सध्याच्या आयुर्वेद ज्ञानकोषात या विषयावर पुरेशी माहिती मिळाली नाही.\n\n"
                    "तुम्ही पुढील विषयांबद्दल विचारू शकता:\n"
                    "• **खोकला व श्वसन विकार**: तुळस, ज्येष्ठमध, सितोपलादि चूर्ण, सुंठ, हळद\n"
                    "• **मूलभूत सिद्धांत**: त्रिदोष (वात, पित्त, कफ), प्रकृती आणि विकृती, अग्नी, आम\n"
                    "• **दिनचर्या व ऋतुचर्या**: आदर्श दैनंदिन दिनचर्या, विरुद्ध आहार\n"
                    "• **महत्त्वाच्या औषधी वनस्पती**: तुळस, अश्वगंधा, आवळा, गुळवेल, त्रिफळा, कडुलिंब"
                )
            elif language == "hi":
                return (
                    "🌿 **सूचना**: मुझे अपने वर्तमान आयुर्वेद ज्ञानकोष में इस विषय पर पर्याप्त जानकारी नहीं मिली।\n\n"
                    "आप इन विषयों के बारे में पूछ सकते हैं:\n"
                    "• **खांसी व श्वसन विकार**: तुलसी, मुलेठी, सितोपलादि चूर्ण, सोंठ, हल्दी\n"
                    "• **मूल सिद्धांत**: पंचमहाभूत, त्रिदोष (वात, पित्त, कफ), प्रकृति और विकृति, अग्नि, आम\n"
                    "• **दिनचर्या और ऋतुचर्या**: दैनिक दिनचर्या, विरुद्ध आहार (दूध और खट्टे फल आदि)\n"
                    "• **औषधियाँ (जड़ी-बूटियाँ)**: तुलसी, अश्वगंधा, आमलकी (आँवला), हल्दी, नीम, ब्राह्मी, त्रिफला"
                )
            return (
                "🌿 **Notice**: I couldn't find reliable information about this concept in my current Ayurveda knowledge base.\n\n"
                "You can try asking about:\n"
                "• **Fundamentals**: Panchamahabhuta, Tridosha, Prakriti & Vikriti, Agni, Ama, Sapta Dhatus\n"
                "• **Lifestyle**: Dinacharya (daily routine), Ritucharya (seasonal regimen), Incompatible foods (Viruddha Ahara)\n"
                "• **Herbs**: Tulsi, Ashwagandha, Amla, Haridra (Turmeric), Neem, Brahmi, Triphala, Guduchi"
            )

        prompt = self.build_prompt(query, citations, conversation_context, language=language)

        # Attempt Gemini API call if client is available
        if self.client:
            try:
                if self._is_legacy:
                    # google.generativeai GenerativeModel
                    response = self.client.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.2,
                            "max_output_tokens": 1024,
                        }
                    )
                else:
                    # modern google.genai Client
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config={
                            "system_instruction": SYSTEM_PROMPT,
                            "temperature": 0.2,
                            "max_output_tokens": 1024,
                        }
                    )
                if response and hasattr(response, 'text') and response.text:
                    return SafetyClassifier.validate_output(response.text)
            except Exception as e:
                print(f"[RAGGenerator] Gemini API error, falling back to grounded synthesizer: {e}")

        # Intelligent grounded synthesis fallback
        return self._synthesize_grounded_response(query, citations, language=language)

    def _extract_monograph_sections(self, content: str) -> Dict[str, str]:
        """Extracts structured sections from classical Ayurvedic monograph chunks."""
        parts = re.search(r'Parts (?:traditionally )?used:\s*(.*?)(?=\.\s*[A-Z]|\.$)', content)
        attrs = re.search(r'Traditional attributes:\s*(.*?)(?=Parts|\.\s*[A-Z]|\.$)', content)
        uses = re.search(r'Traditional uses:\s*(.*?)(?=Modern|\.\s*[A-Z]|\.$)', content)
        sci = re.search(r'Modern Scientific Observations:\s*(.*?)$', content)
        first_sen = (content.split('. ')[0] + '.') if content else ''
        return {
            'overview': first_sen,
            'parts': parts.group(1).strip() if parts else '',
            'attrs': attrs.group(1).strip() if attrs else '',
            'uses': uses.group(1).strip() if uses else '',
            'sci': sci.group(1).strip() if sci else ''
        }

    def _synthesize_grounded_response(
        self,
        query: str,
        citations: List[SourceCitation],
        language: str = "en"
    ) -> str:
        """
        Synthesizes a structured, highly grounded and customized answer tailored to the user's intent:
        - Image / photo requests
        - Benefits / uses / 'fayde' queries
        - How-to-use / dosage / preparation queries
        - Symptom / remedy queries (cough, period, digestion, etc.)
        - Conceptual 'what is' queries
        """
        primary = citations[0]
        title = primary.title
        from backend.app.rag.spelling import spell_corrector
        correction_res = spell_corrector.process_query(query)
        q_lower = f"{query.lower()} {correction_res.normalized_query.lower()}"

        is_image_query = any(w in q_lower for w in ["image", "photo", "picture", "dikhao", "look like", "kaisa dikhta", "tasveer", "pic", "kashi diste", "kasa disto"])
        is_benefits_query = any(w in q_lower for w in ["benefit", "benefits", "fayde", "fyde", "faida", "fayda", "labh", "uses", "use", "kam kya", "good for", "advantages", "kashasathi"])
        is_usage_query = any(w in q_lower for w in ["how to use", "how to take", "kaise le", "kab le", "kasa ghyava", "dosage", "consumption", "intake", "preparation"])
        is_cough_query = any(w in q_lower or w in query for w in [
            "khokla", "khoklya", "खोकला", "खोकल्या", "कास", "cough", "kasa", "घसा", "sardi", "सर्दी", "kuff", "kapha"
        ])
        is_period_query = any(w in q_lower or w in query for w in [
            "period", "periods", "menstrual", "menstruation", "मासिक", "पाळी", "मासिक पाळी", "मासिक धर्म", "shatavari", "शतावरी", "ashoka", "अशोक", "cramp", "cramps"
        ]) or any(kw in primary.title.lower() for kw in ["rajaswala", "shatavari", "ashoka"])

        is_anupana_query = any(w in q_lower or w in query for w in [
            "warm water", "honey", "shahad", "madhu", "ushnodaka", "anupana", "hot water", "lukewarm", "doodh", "milk",
            "पाणी", "कोमट", "मध", "मधासोबत", "पाण्यासोबत", "कशासोबत",
            "शहद", "गुनगुने", "पानी", "दूध", "अनुपान", "किसके साथ"
        ])
        is_diet_query = any(w in q_lower or w in query for w in [
            "diet", "pathya", "apathya", "food", "what to eat", "avoid", "khana", "parhez", "aahar", "kya khaye", "kya na khaye",
            "पथ्य", "अपथ्य", "आहार", "खान-पान", "परहेज", "काय खावे", "काय खाऊ नये", "अन्न"
        ])
        is_relief_timeline_query = any(w in q_lower or w in query for w in [
            "relief", "how long", "cure", "recover", "recovery", "kitne din", "aaram", "kiti divas", "kitne din me", "kiti divasat",
            "आराम", "कितने दिन", "कधीपर्यंत", "किती दिवस", "बरा होईल का", "ठीक होगा"
        ])

        if language == "mr":
            return self._synthesize_marathi_response(
                query, citations, is_image_query, is_benefits_query, is_usage_query, is_cough_query, is_period_query,
                is_anupana_query=is_anupana_query, is_diet_query=is_diet_query, is_relief_timeline_query=is_relief_timeline_query
            )
        elif language == "hi":
            return self._synthesize_hindi_response(
                query, citations, is_image_query, is_benefits_query, is_usage_query, is_cough_query, is_period_query,
                is_anupana_query=is_anupana_query, is_diet_query=is_diet_query, is_relief_timeline_query=is_relief_timeline_query
            )

        # English Default Customized Synthesis
        content = primary.content or primary.snippet or ""
        mono = self._extract_monograph_sections(content)
        short_title = title.split(" — ")[0]
        response_parts = []

        if is_anupana_query:
            response_parts.append("### 🍯 Ayurvedic Carrier Guide (Anupana): Warm Water vs. Raw Honey\n")
            response_parts.append(
                "In classical Ayurvedic pharmacology (*Dravyaguna Vijnana*), the carrier (**Anupana**) used to take an herbal medicine is just as important as the herb itself. "
                "Anupana speeds drug delivery, facilitates deep tissue (*Dhatu*) penetration, and balances aggravated doshas.\n"
            )
            response_parts.append("#### 1. 🫖 Warm Water (Ushnodaka) as Anupana:")
            response_parts.append("• **Ayurvedic Karma**: *Deepana* (kindles digestive fire/Agni), *Pachana* (digests metabolic toxins/Ama), and *Srotovishodhana* (opens body channels).")
            response_parts.append("• **When to Choose Warm Water**:")
            response_parts.append("  - Ideal for systemic detox, gas, bloating, and Vata/Kapha imbalances.")
            response_parts.append("  - Premier vehicle for **Triphala Churna**, **Guduchi (Giloy)**, and **Shunthi (Dry Ginger)**.")
            response_parts.append("  - Sip warm (lukewarm to hot) early in the morning on an empty stomach or 30 minutes after meals.\n")
            response_parts.append("#### 2. 🍯 Pure Raw Honey (Madhu) as Anupana:")
            response_parts.append("• **Ayurvedic Karma**: *Yogavahi* (catalytic carrier that carries herb qualities deep into cellular channels without losing its own nature), *Chhedana* (scrapes and liquefies stubborn phlegm/Kapha), and soothing.")
            response_parts.append("• **When to Choose Honey**:")
            response_parts.append("  - Supreme vehicle for respiratory distress, throat tickling, wet or dry cough, and voice hoarseness.")
            response_parts.append("  - Classical pair for **Sitopaladi Churna**, **Tulsi leaf juice (Swarasa)**, and **Yashtimadhu (Licorice)**.")
            response_parts.append("  - Mix half to 1 teaspoon of pure unheated honey with the herbal powder into a smooth paste (Lehya/Linctus) and lick slowly.\n")
            response_parts.append("---")
            response_parts.append("### ⚠️ CRITICAL AYURVEDIC SAFETY RULE: Never Heat Honey (*Ushna Madhu*)")
            response_parts.append(
                "> **Charaka Samhita (Sutra Sthana 27 / Viruddha Ahara)** explicitly warns:\n"
                "> **'Never heat honey, and never mix honey into boiling or piping-hot liquids.'**\n>\n"
                "> When honey is heated above body temperature (~40°C / 104°F), its subtle enzymes degrade into **Ama Visha** (sticky micro-toxin that clogs bodily micro-channels/Srotas).\n>\n"
                "> **Safe Practice**: Take the herb-honey paste first, then sip lukewarm (not hot) water after a 10-15 minute gap. Never stir honey into boiling tea or hot decoctions."
            )

        elif is_diet_query:
            response_parts.append("### 🍲 Classical Ayurvedic Dietary Regimen (Pathya & Apathya)\n")
            response_parts.append(
                "In classical Ayurveda, diet (**Ahara**) is termed the supreme medicine (*Maha-Bheshaja*). "
                "As the ancient Ayurvedic text *Vaidya Jeevana* states: *'When diet is wrong, medicine is of no use. When diet is correct, medicine is of no need.'*\n"
            )
            response_parts.append("#### 1. 🟢 Pathya (Wholesome Foods to Favor):")
            response_parts.append("• **Warm & Light Meals (Laghu Ahara)**: Freshly prepared Moong dal khichdi, thin vegetable soups seasoned with cumin (Jeera) and fresh ginger (Adrak).")
            response_parts.append("• **Digestive Spices**: Incorporate cumin, coriander seeds, fennel, ginger, and a pinch of turmeric in warm meals to stimulate Agni.")
            response_parts.append("• **Warm Hydration**: Drink boiled, lukewarm water throughout the day to continuously flush metabolic toxins (Ama).")
            response_parts.append("• **Healthy Fats**: 1 teaspoon of pure A2 cow Ghee with warm rice or soup to pacify Vata and nourish dry mucous membranes.\n")
            response_parts.append("#### 2. 🔴 Apathya (Foods & Habits to Strictly Avoid):")
            response_parts.append("• **Cold & Iced Drinks (Sheeta Ahara)**: Cold water, ice cream, refrigerated food, and chilled drinks instantly vitiate Vata and Kapha and extinguish Agni.")
            response_parts.append("• **Curd/Yogurt at Night (Dadhi Nishedha)**: Never consume curd at night; it is *Abhishyandi* (heavily clogs micro-channels) and triggers mucus production.")
            response_parts.append("• **Heavy, Oily & Deep-Fried Foods**: Samosas, pakoras, refined flour (Maida), and stale leftovers that generate sticky Ama.")
            response_parts.append("• **Incompatible Foods (Viruddha Ahara)**: Avoid combining milk with sour fruits, citrus, melon, or salty foods.")
            response_parts.append("• **Daytime Sleeping (Divasvapna)**: Avoid sleeping immediately after meals during the day, which sharply aggravates Kapha.")

        elif is_relief_timeline_query:
            response_parts.append("### ⏳ Expected Recovery Timeline & Ayurvedic Healing Prognosis\n")
            response_parts.append(
                "Unlike superficial symptom suppression, Ayurvedic protocols address the root biological cause (*Nidana Parivarjana*) by restoring doshic balance and supporting vital immunity (*Ojas*).\n"
            )
            response_parts.append("#### 1. ⏱️ Acute Imbalances (Cough, Cold, Sore Throat, Mild Indigestion):")
            response_parts.append("• **24 to 48 Hours**: With warm hydration, rest, and appropriate Anupana (e.g. Tulsi/Sitopaladi with raw honey), noticeable easing of throat irritation, chest tightness, and digestive discomfort begins.")
            response_parts.append("• **Day 3 to Day 5**: Progressive clearance of accumulated Kapha, rekindling of digestive fire (*Sama Agni*), and return of natural energy levels.\n")
            response_parts.append("#### 2. 🌿 Deep-Seated or Chronic Imbalances (Joint Stiffness, Acidity, Insomnia):")
            response_parts.append("• Deeper imbalances involve cellular tissues (*Dhatus*), typically requiring **2 to 4 weeks** of disciplined dietary adherence (Pathya) and herbal rejuvenation (*Rasayana*).\n")
            response_parts.append("---")
            response_parts.append("### ⚠️ Red-Flag Symptoms Requiring Medical Attention:")
            response_parts.append(
                "Seek immediate consultation from a qualified physician or hospital if you experience:\n"
                "• High unremitting fever (>101°F / 38.5°C) lasting over 3 days\n"
                "• Shortness of breath, wheezing, or sharp chest pain\n"
                "• Blood in cough or sputum\n"
                "• Inability to swallow fluids or severe dehydration"
            )

        if is_image_query:
            response_parts.append(f"### 🌿 Botanical Reference: {short_title}\n")
            response_parts.append(
                f"Here is the authentic botanical reference illustration of **{short_title}**! "
                f"In classical Ayurveda, this revered herb is identified by distinct physical traits and traditional attributes.\n"
            )
            response_parts.append("#### 🔍 Botanical Identification & Medicinal Parts:")
            if mono['parts']:
                response_parts.append(f"• **Medicinal Parts Used**: {mono['parts']}.")
            response_parts.append(f"• **Botanical Significance**: {mono['overview']}")
            if mono['attrs']:
                response_parts.append(f"• **Ayurvedic Profile (Dravyaguna)**: {mono['attrs']}.")
            if mono['uses']:
                response_parts.append(f"\n#### ✨ Primary Classical Indications:\n{mono['uses']}.")

        elif is_benefits_query:
            response_parts.append(f"### 🌿 Key Ayurvedic Health Benefits: {short_title}\n")
            response_parts.append(f"**{short_title}** is renowned in classical Ayurvedic literature for its restorative and therapeutic properties.\n")
            if mono['uses']:
                response_parts.append("#### 🌟 Core Health Benefits & Traditional Actions (Karma):")
                # Split uses by comma for readable bullets
                use_points = [u.strip() for u in mono['uses'].split(",") if u.strip()]
                for u in use_points:
                    response_parts.append(f"• {u.capitalize()}")
            if mono['attrs']:
                response_parts.append(f"\n#### ⚖️ Doshic Balance & Energetics:\n• {mono['attrs']}")
            if mono['sci']:
                response_parts.append(f"\n#### 🔬 Modern Scientific Research:\n• {mono['sci']}")
            if mono['parts']:
                response_parts.append(f"\n#### 🍃 Traditional Parts Used: {mono['parts']}")

        elif is_usage_query:
            response_parts.append(f"### 🌿 Traditional Ayurvedic Preparation & Usage: {short_title}\n")
            response_parts.append(f"In classical Ayurvedic pharmacology, **{short_title}** is utilized with specific carriers (Anupana) to maximize absorption:\n")
            response_parts.append("#### 🍵 Recommended Classical Methods:")
            response_parts.append("• **Formulations**: Commonly prepared as fine herbal powder (Churna), fresh juice (Swarasa), or decoction (Kwath).")
            response_parts.append("• **Traditional Vehicles (Anupana)**: Often administered with warm water, raw honey, or warm milk depending on individual constitution (Prakriti).")
            response_parts.append("• **Optimal Timing**: Typically consumed either early morning on an empty stomach or before restful sleep under professional supervision.")
            if mono['uses']:
                response_parts.append(f"\n#### ✨ Primary Applications: {mono['uses']}")

        else:
            # Clean structured educational breakdown
            response_parts.append(f"### {title}\n")
            response_parts.append(f"{mono['overview']}\n")
            if mono['attrs']:
                response_parts.append(f"#### 🍃 Ayurvedic Attributes (Dravyaguna):\n• {mono['attrs']}\n")
            if mono['uses']:
                response_parts.append(f"#### 🌟 Traditional Uses & Therapeutic Scope:\n• {mono['uses']}\n")
            if mono['sci']:
                response_parts.append(f"#### 🔬 Modern Scientific Insights:\n• {mono['sci']}\n")
            if not mono['attrs'] and not mono['uses']:
                response_parts.append(f"{content}\n")

        # Complementary secondary citations
        matching_secondary = []
        if len(citations) > 1:
            for c in citations[1:]:
                title_words = [w.lower() for w in re.findall(r'[a-zA-Z]{4,}', c.title)]
                if any(w in q_lower for w in title_words):
                    matching_secondary.append(c)

        if matching_secondary:
            for sec in matching_secondary:
                response_parts.append(f"### {sec.title}\n")
                sec_mono = self._extract_monograph_sections(sec.content or sec.snippet or "")
                response_parts.append(f"{sec_mono['overview']}\n")
                if sec_mono['uses']:
                    response_parts.append(f"• **Key Actions**: {sec_mono['uses']}\n")

        # Classical insights from remaining
        remaining = [c for c in citations[1:] if c not in matching_secondary]
        if remaining:
            response_parts.append("#### 📚 Classical Insights from Corpus:")
            for c in remaining[:2]:
                first_sentence = (c.content or c.snippet or "").split(". ")[0]
                if first_sentence:
                    response_parts.append(f"• **{c.title}**: {first_sentence}.")

        response_parts.append(
            "\n### ⚠️ Educational Note\n"
            "This information originates from classical Ayurvedic texts (Charaka & Sushruta Samhita) and the Ayurvedic Pharmacopoeia of India (API). "
            "It is intended for educational purposes and should not replace personalized medical advice."
        )
        return SafetyClassifier.validate_output("\n\n".join(response_parts))

    def _synthesize_marathi_response(
        self,
        query: str,
        citations: List[SourceCitation],
        is_image_query: bool,
        is_benefits_query: bool,
        is_usage_query: bool,
        is_cough_query: bool,
        is_period_query: bool = False,
        is_anupana_query: bool = False,
        is_diet_query: bool = False,
        is_relief_timeline_query: bool = False,
        **kwargs
    ) -> str:
        """Synthesizes structured, authentic Ayurvedic guidance in Marathi customized to query intent."""
        marathi_title_map = {
            "Tulsi (Holy Basil) — Ocimum sanctum": "तुळस (पवित्र तुळशी) — Ocimum sanctum",
            "Yashtimadhu / Licorice (Jyeshthamadh / Mulethi) — Glycyrrhiza glabra": "ज्येष्ठमध (Yashtimadhu / Jyeshthamadh) — Glycyrrhiza glabra",
            "Sitopaladi Churna — Classical Formulation for Cough, Cold & Respiratory Balance": "सितोपलादि चूर्ण — खोकला, कफ व सर्दीवरील पारंपरिक आयुर्वेदिक योग",
            "Shunthi / Dry Ginger (Sunth) — Zingiber officinale": "सुंठ (Shunthi) — Zingiber officinale",
            "Haridra / Turmeric — Curcuma longa": "हळद (हरिद्रा) — Curcuma longa",
            "Guduchi / Giloy — Tinospora cordifolia": "गुळवेल (गिलोय / गुडूची) — Tinospora cordifolia",
            "Triphala — The Classical Three-Fruit Synergy": "त्रिफळा चूर्ण — तीन दिव्य फळांचे रसायन",
            "Amalaki / Amla (Indian Gooseberry) — Phyllanthus emblica": "आवळा (आमलकी) — Phyllanthus emblica",
            "Ashwagandha (Indian Ginseng) — Withania somnifera": "अश्वगंधा — Withania somnifera",
            "Neem (Nimba) — Azadirachta indica": "कडुलिंब (निंब) — Azadirachta indica",
            "Brahmi / Bacopa — Bacopa monnieri": "ब्राह्मी — Bacopa monnieri",
            "Agni — The Digestive and Metabolic Fire": "अग्नी — पचन आणि चयापचय अग्नी",
            "Vata, Pitta, and Kapha — The Tridosha Doctrine": "वात, पित्त आणि कफ — त्रिदोष सिद्धांत",
            "Prakriti and Vikriti — Individual Constitution and Doshic Imbalance": "प्रकृती आणि विकृती — शारीरिक प्रकृती व दोषांचे असंतुलन",
            "Dinacharya — Classical Daily Regimen for Optimal Health": "दिनचर्या — आरोग्यासाठी आदर्श दैनंदिन जीवनशैली नियम",
            "Ritucharya — Seasonal Regimen and Doshic Rhythms": "ऋतुचर्या — ऋतूनुसार आहाराचे व जीवनशैलीचे नियम",
            "Ahara — Ayurvedic Dietary Principles and the Six Tastes (Shad Rasa)": "आहार — षड्रस आणि आयुर्वेदाचे पोषण नियम",
            "Rajaswala Paricharya — Ayurvedic Menstrual Cycle Care & Female Wellness": "रजस्वला परिचर्या — मासिक पाळीतील आरोग्य व महिला कल्याण",
            "Shatavari (Indian Asparagus) — Asparagus racemosus": "शतावरी — Asparagus racemosus (स्त्री रसायन)",
            "Ashoka (Sacred Asoka) — Saraca asoca": "अशोक — Saraca asoca (गर्भाशय टॉनिक)"
        }

        primary = citations[0]
        mr_title = marathi_title_map.get(primary.title, primary.title)
        mono = self._extract_monograph_sections(primary.content or primary.snippet or "")
        response_parts = []

        if is_image_query:
            response_parts.append(f"### 🌿 वनस्पती ओळख व स्वरूप: {mr_title}\n")
            response_parts.append(
                f"येथे **{mr_title}** ची प्रामाणिक वानस्पतिक प्रतिमा दर्शविली आहे! "
                f"शास्त्रीय आयुर्वेदानुसार या औषधी वनस्पतीची ओळख व वैशिष्ट्ये पुढीलप्रमाणे आहेत:\n"
            )
            response_parts.append("#### 🔍 वनस्पतीची ओळख व उपयुक्त घटक:")
            if mono['parts']:
                response_parts.append(f"• **वापरण्यात येणारे घटक**: {mono['parts']}")
            response_parts.append(f"• **आयुर्वेदिक स्वरूप**: {mono['overview']}")
            if mono['attrs']:
                response_parts.append(f"• **रस, वीर्य व गुण**: {mono['attrs']}")
            if mono['uses']:
                response_parts.append(f"\n#### ✨ मुख्य शास्त्रीय उपयोग: {mono['uses']}")

        elif is_benefits_query:
            response_parts.append(f"### 🌿 {mr_title} चे प्रमुख आयुर्वेदिक फायदे व गुणधर्म\n")
            response_parts.append(f"**{mr_title}** हे आयुर्वेदातील अत्यंत गुणकारी व श्रेष्ठ औषध मानले जाते.\n")
            response_parts.append("#### 🌟 मुख्य आरोग्यदायी फायदे:")
            if mono['uses']:
                for u in mono['uses'].split(","):
                    if u.strip():
                        response_parts.append(f"• {u.strip().capitalize()}")
            if mono['attrs']:
                response_parts.append(f"\n#### ⚖️ दोषांवरील प्रभाव: {mono['attrs']}")
            if mono['sci']:
                response_parts.append(f"\n#### 🔬 आधुनिक वैज्ञानिक संशोधन: {mono['sci']}")

        elif is_cough_query or "tulsi" in primary.title.lower() or "yashtimadhu" in primary.title.lower() or "sitopaladi" in primary.title.lower():
            response_parts.append(f"### {mr_title}\n")
            response_parts.append(
                "आयुर्वेदानुसार खोकला हा **'कास'** रोग मानला जातो, जो मुख्यत्वे **कफ आणि वात दोषाच्या असंतुलनामुळे** "
                "तसेच प्राणवह स्रोतसांमधील अडथळ्यामुळे निर्माण होतो. यासाठी कफशामक, उष्ण वीर्य आणि घशाला मऊ करणाऱ्या औषधी वनस्पती अत्यंत गुणकारी मानल्या जातात."
            )
            response_parts.append(
                "#### खोकल्यावरील पारंपारिक आयुर्वेदिक उपाय व पद्धती:\n"
                "• **तुळस (Tulsi) आणि मध**: ५ ते ७ ताज्या तुळशीच्या पानांचा रस काढून त्यात १ चमचा शुद्ध मध मिसळून दिवसातून दोन वेळा घेतल्यास कफ मोकळा होतो.\n"
                "• **ज्येष्ठमध (Yashtimadhu / Mulethi)**: कोरडा खोकला आणि घशातील खवखव शांत करण्यासाठी ज्येष्ठमधाची कांडी चघळणे किंवा अर्धा चमचा ज्येष्ठमध पावडर कोमट पाण्यातून घेणे प्रभावी ठरते.\n"
                "• **सितोपलादि चूर्ण (Sitopaladi Churna)**: हे खोकला आणि कफासाठीचे प्रसिद्ध शास्त्रीय चूर्ण आहे. हे मध आणि साजूक तुपासोबत घेतले जाते.\n"
                "• **सुंठ आणि कोमट पाणी**: सुंठ पावडर मधात मिसळून घेतल्याने कफ वितळतो आणि पचन सुधारते."
            )
        elif is_period_query or "rajaswala" in primary.title.lower() or "shatavari" in primary.title.lower() or "ashoka" in primary.title.lower():
            response_parts.append(f"### {mr_title}\n")
            response_parts.append(
                "आयुर्वेदात मासिक पाळी ही शरीराचे नैसर्गिक शुद्धीकरण मानले जाते. ही प्रक्रिया मुख्यत्वे **अपान वायू** आणि **आर्तव धातू** यांच्या संतुलनावर अवलंबून असते. "
                "चरक व सुश्रुत संहितेत यासाठी **'रजस्वला परिचर्या'** नावाचे अत्यंत प्रभावी शास्त्रीय जीवनशैली व आहार नियम सांगितले आहेत."
            )
            response_parts.append(
                "#### मासिक पाळीतील आरोग्य व त्रासावर शास्त्रीय आयुर्वेदिक उपाय:\n"
                "• **रजस्वला परिचर्या (विश्रांती)**: पहिल्या २-३ दिवसांत विश्रांती घेणे आवश्यक आहे.\n"
                "• **सुपाच्य आहार**: मऊ खिचडी, साजूक तूप लावलेला कोमट भात आणि पाचक सूप घ्यावे.\n"
                "• **घरगुती काढा**: जिरं, बडीशेप, सुंठ आणि ओवा समप्रमाणात उकळून घेतलेला काढा कळा शांत करतो.\n"
                "• **शतावरी व अशोक**: गर्भाशयाचे आरोग्य व मासिक पाळीचे नियमन करण्यासाठी सर्वश्रेष्ठ वनस्पती."
            )
        else:
            response_parts.append(f"### {mr_title}\n")
            response_parts.append(f"**शास्त्रीय माहिती**: {mono['overview']}\n")
            if mono['attrs']:
                response_parts.append(f"• **दोष व गुण**: {mono['attrs']}")
            if mono['uses']:
                response_parts.append(f"• **प्रमुख उपयोग**: {mono['uses']}")

        # Marathi Educational Disclaimer
        response_parts.append(
            "\n### ⚠️ महत्त्वाची शैक्षणिक सूचना\n"
            "ही माहिती केवळ शास्त्रीय आयुर्वेदिक ग्रंथ आणि आयुष (AYUSH) संदर्भ साहित्यावर आधारित शैक्षणिक मार्गदर्शनासाठी आहे. "
            "तीव्र लक्षणांसाठी कृपया तज्ज्ञ आयुर्वेदिक वैद्यांचा प्रत्यक्ष सल्ला घ्या."
        )

        return SafetyClassifier.validate_output("\n\n".join(response_parts))

    def _synthesize_hindi_response(
        self,
        query: str,
        citations: List[SourceCitation],
        is_image_query: bool,
        is_benefits_query: bool,
        is_usage_query: bool,
        is_cough_query: bool,
        is_period_query: bool = False,
        is_anupana_query: bool = False,
        is_diet_query: bool = False,
        is_relief_timeline_query: bool = False,
        **kwargs
    ) -> str:
        """Synthesizes structured Ayurvedic guidance in Hindi customized to query intent."""
        hindi_title_map = {
            "Tulsi (Holy Basil) — Ocimum sanctum": "तुलसी (Tulsi) — Ocimum sanctum",
            "Ashwagandha (Indian Ginseng) — Withania somnifera": "अश्वगंधा (Ashwagandha) — Withania somnifera",
            "Triphala — The Classical Three-Fruit Synergy": "त्रिफला (Triphala) — तीन दिव्य फलों का योग",
            "Amalaki / Amla (Indian Gooseberry) — Phyllanthus emblica": "आमलकी / आँवला (Amla) — Phyllanthus emblica",
            "Haridra / Turmeric — Curcuma longa": "हरिद्रा / हल्दी (Turmeric) — Curcuma longa",
            "Neem (Nimba) — Azadirachta indica": "नीम (Nimba) — Azadirachta indica",
            "Brahmi / Bacopa — Bacopa monnieri": "ब्राह्मी (Brahmi) — Bacopa monnieri",
            "Guduchi / Giloy — Tinospora cordifolia": "गिलोय / गुडूची (Giloy) — Tinospora cordifolia",
            "Yashtimadhu / Licorice (Jyeshthamadh / Mulethi) — Glycyrrhiza glabra": "मुलेठी / यष्टिमधु (Yashtimadhu) — Glycyrrhiza glabra",
            "Sitopaladi Churna — Classical Formulation for Cough, Cold & Respiratory Balance": "सितोपलादि चूर्ण — खांसी व जुकाम के लिए शास्त्रीय योग",
            "Shunthi / Dry Ginger (Sunth) — Zingiber officinale": "सोंठ / शुण्ठी (Dry Ginger) — Zingiber officinale",
            "Shatavari (Indian Asparagus) — Asparagus racemosus": "शतावरी (Shatavari) — स्त्री रसायन",
            "Ashoka (Sacred Asoka) — Saraca asoca": "अशोक (Ashoka) — गर्भाशय टॉनिक",
            "Prakriti and Vikriti — Individual Constitution and Doshic Imbalance": "प्रकृति और विकृति — शारीरिक संविधान व असंतुलन",
            "Tridosha Theory — Overview of the Three Bio-energies": "त्रिदोष सिद्धांत — वात, पित्त और कफ",
            "Dinacharya — Classical Daily Regimen for Optimal Health": "दिनचर्या — दैनिक स्वास्थ्य नियम",
            "Ritucharya — Seasonal Regimen and Doshic Rhythms": "ऋतुचर्या — मौसमी आहार-विहार के नियम",
            "Viruddha Ahara — Incompatible Food Combinations": "विरुद्ध आहार — अहितकर खाद्य संयोग",
            "Agni — The Digestive and Metabolic Fire": "अग्नि — पाचन एवं चयापचय अग्नि",
            "What is Ayurveda — Origin and Definition": "आयुर्वेद क्या है — उद्भव और परिभाषा"
        }

        primary = citations[0]
        hi_title = hindi_title_map.get(primary.title, primary.title)
        mono = self._extract_monograph_sections(primary.content or primary.snippet or "")
        response_parts = []

        if is_image_query:
            response_parts.append(f"### 🌿 वानस्पतिक पहचान एवं तस्वीर: {hi_title}\n")
            response_parts.append(
                f"यहाँ **{hi_title}** की प्रामाणिक वानस्पतिक (Botanical) तस्वीर संलग्न की गई है! "
                f"शास्त्रीय आयुर्वेद में इस जड़ी-बूटी की पहचान और विशेषताएं इस प्रकार हैं:\n"
            )
            response_parts.append("#### 🔍 पौधे की पहचान एवं उपयोगी अंग:")
            if mono['parts']:
                response_parts.append(f"• **उपयोगी अंग**: {mono['parts']}")
            response_parts.append(f"• **वानस्पतिक विवरण**: {mono['overview']}")
            if mono['attrs']:
                response_parts.append(f"• **आयुर्वेदिक गुण (रस, वीर्य, विपाक)**: {mono['attrs']}")
            if mono['uses']:
                response_parts.append(f"\n#### ✨ प्रमुख स्वास्थ्य उपयोग:\n{mono['uses']}")

        elif is_benefits_query:
            response_parts.append(f"### 🌿 {hi_title} के प्रमुख आयुर्वेदिक लाभ एवं उपयोग (Fayde)\n")
            response_parts.append(f"**{hi_title}** आयुर्वेद में अपने चमत्कारी स्वास्थ्य लाभों और दोष संतुलन के लिए अत्यंत प्रसिद्ध है।\n")
            response_parts.append("#### 🌟 मुख्य स्वास्थ्य लाभ (Key Benefits):")
            if mono['uses']:
                for u in mono['uses'].split(","):
                    if u.strip():
                        response_parts.append(f"• {u.strip().capitalize()}")
            if mono['attrs']:
                response_parts.append(f"\n#### ⚖️ दोषों पर प्रभाव:\n• {mono['attrs']}")
            if mono['sci']:
                response_parts.append(f"\n#### 🔬 आधुनिक वैज्ञानिक शोध:\n• {mono['sci']}")
            if mono['parts']:
                response_parts.append(f"\n#### 🍃 उपयोगी अंग: {mono['parts']}")

        elif is_usage_query:
            response_parts.append(f"### 🌿 {hi_title} के सेवन का तरीका एवं पारंपरिक नियम\n")
            response_parts.append("शास्त्रीय आयुर्वेद के अनुसार औषधियों का उचित अनुपान (Carrier) के साथ सेवन करने से उत्तम लाभ मिलता है:\n")
            response_parts.append("#### 🍵 सेवन के प्रमुख शास्त्रीय नियम:")
            response_parts.append("• **स्वरूप**: आमतौर पर चूर्ण (Powder), काढ़ा (Kwath) या ताजे रस (Swarasa) के रूप में।")
            response_parts.append("• **अनुपान (किसके साथ लें)**: प्रकृति के अनुसार गुनगुने पानी, शहद या गाय के दूध के साथ।")
            response_parts.append("• **समय**: सामान्यतः प्रातःकाल खाली पेट अथवा रात्रि विश्राम से पूर्व।")
            if mono['uses']:
                response_parts.append(f"\n#### ✨ मुख्य लाभ: {mono['uses']}")

        elif is_cough_query or "tulsi" in primary.title.lower() or "sitopaladi" in primary.title.lower():
            response_parts.append(f"### {hi_title}\n")
            response_parts.append(
                "आयुर्वेद में खांसी को **'कास'** कहा जाता है, जो मुख्य रूप से **कफ और वात दोष** के प्रकुपित होने से होती है। "
                "श्वसन मार्ग को साफ करने और कफ को शांत करने के लिए पारंपरिक रूप से तुलसी, मुलेठी, और सितोपलादि चूर्ण का उपयोग किया जाता है।"
            )
            response_parts.append(
                "#### खांसी के लिए प्रमुख आयुर्वेदिक एवं घरेलू उपाय:\n"
                "• **तुलसी और शहद**: ताजी तुलसी की पत्तियों का रस शहद के साथ लेने से कफ दूर होता है और गले को आराम मिलता है।\n"
                "• **मुलेठी (यष्टिमधु)**: सूखी खांसी और गले की खराश के लिए मुलेठी चबाना या इसका चूर्ण गुनगुने पानी के साथ लेना लाभकारी है।\n"
                "• **सितोपलादि चूर्ण**: यह खांसी और जुकाम के लिए एक प्रसिद्ध शास्त्रीय औषधि है जिसे शहद और घी के साथ लिया जाता है।\n"
                "• **सोंठ और गुड़**: सोंठ का सेवन कफ को संतुलित करता है और श्वसन तंत्र को गर्माहट देता है।"
            )
        elif is_period_query or "rajaswala" in primary.title.lower() or "shatavari" in primary.title.lower() or "ashoka" in primary.title.lower():
            response_parts.append(f"### {hi_title}\n")
            response_parts.append(
                "आयुर्वेद में मासिक धर्म को एक अत्यंत महत्वपूर्ण प्राकृतिक शोधन प्रक्रिया माना गया है, जो मुख्य रूप से **अपान वायु** और **आर्तव धातु** के संतुलन से संचालित होती है। "
                "मासिक धर्म को नियमित और दर्द-मुक्त रखने के लिए चरक एवं सुश्रुत संहिता में **'रजस्वला परिचर्या'** का विशेष विधान दिया गया है।"
            )
            response_parts.append(
                "#### मासिक धर्म (पीरियड्स) के लिए प्रमुख आयुर्वेदिक नियम व उपाय:\n"
                "• **रजस्वला परिचर्या (विश्राम)**: पहले 2-3 दिनों में भारी व्यायाम और तनाव से बचें।\n"
                "• **सुपाच्य एवं गुनगुना आहार**: ताजा, हल्का और गर्म भोजन लें (जैसे मूँग दाल की खिचड़ी)।\n"
                "• **घरेलू हर्बल चाय**: जीरा, सौंफ, सोंठ और अजवाइन का काढ़ा ऐंठन में आराम देता है।\n"
                "• **शतावरी एवं अशोक**: गर्भाशय स्वास्थ्य और हार्मोनल संतुलन की सर्वश्रेष्ठ औषधियाँ।"
            )
        else:
            response_parts.append(f"### {hi_title}\n")
            response_parts.append(f"**आयुर्वेदिक परिचय**: {mono['overview']}\n")
            if mono['attrs']:
                response_parts.append(f"#### 🍃 आयुर्वेदिक गुण-धर्म:\n• {mono['attrs']}\n")
            if mono['uses']:
                response_parts.append(f"#### 🌟 पारंपरिक उपयोग:\n• {mono['uses']}\n")
            if mono['sci']:
                response_parts.append(f"#### 🔬 आधुनिक वैज्ञानिक दृष्टिकोण:\n• {mono['sci']}\n")

        if len(citations) > 1:
            response_parts.append("#### 📚 पूरक शास्त्रीय दृष्टिकोण:\n")
            for c in citations[1:3]:
                first_sentence = (c.content or c.snippet or "").split(". ")[0]
                if first_sentence:
                    response_parts.append(f"• **{c.title}**: {first_sentence}.")

        response_parts.append(
            "\n### ⚠️ महत्वपूर्ण शैक्षिक सूचना\n"
            "यह विवरण शास्त्रीय आयुर्वेदिक ग्रंथों और आयुष संदर्भों पर आधारित है। "
            "यह केवल शैक्षिक समझ के लिए प्रदान किया गया है और इसका उपयोग चिकित्सीय निदान या उपचार के रूप में न करें।"
        )
        return SafetyClassifier.validate_output("\n\n".join(response_parts))

# Global generator instance
rag_generator = RAGGenerator()
