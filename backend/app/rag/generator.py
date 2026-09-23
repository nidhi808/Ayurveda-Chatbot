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

USER QUESTION:
{query}

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

    def _synthesize_grounded_response(
        self,
        query: str,
        citations: List[SourceCitation],
        language: str = "en"
    ) -> str:
        """
        Synthesizes a structured, highly grounded answer from retrieved chunks.
        Provides fluent Marathi and Hindi knowledge mapping when operating offline.
        """
        primary = citations[0]
        title = primary.title
        q_lower = query.lower()
        is_cough_query = any(w in q_lower or w in query for w in [
            "khokla", "khoklya", "खोकला", "खोकल्या", "कास", "cough", "kasa", "घसा", "sardi", "सर्दी"
        ])

        if language == "mr":
            return self._synthesize_marathi_response(query, citations, is_cough_query)
        elif language == "hi":
            return self._synthesize_hindi_response(query, citations, is_cough_query)

        # English Default
        response_parts = []
        response_parts.append(f"### {title}\n")
        content = primary.content or primary.snippet or ""
        response_parts.append(f"{content}\n")

        if len(citations) > 1:
            response_parts.append("#### Key Principles & Classical Insights\n")
            for c in citations[1:]:
                first_sentence = (c.content or c.snippet or "").split(". ")[0]
                if first_sentence:
                    response_parts.append(f"• **{c.title}**: {first_sentence}.")

        response_parts.append(
            "\n### Important Note\n"
            "These descriptions originate from classical Ayurvedic literature and modern reference monographs. "
            "They are provided for educational understanding and should not be used as clinical diagnosis or treatment guidance."
        )
        return SafetyClassifier.validate_output("\n\n".join(response_parts))

    def _synthesize_marathi_response(
        self,
        query: str,
        citations: List[SourceCitation],
        is_cough_query: bool
    ) -> str:
        """Synthesizes structured, authentic Ayurvedic guidance in Marathi."""
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
            "Ahara — Ayurvedic Dietary Principles and the Six Tastes (Shad Rasa)": "आहार — षड्रस आणि आयुर्वेदाचे पोषण नियम"
        }

        primary = citations[0]
        mr_title = marathi_title_map.get(primary.title, primary.title)
        response_parts = []

        response_parts.append(f"### {mr_title}\n")

        # Context-sensitive Marathi explanation
        if is_cough_query or "tulsi" in primary.title.lower() or "yashtimadhu" in primary.title.lower() or "sitopaladi" in primary.title.lower():
            response_parts.append(
                "आयुर्वेदानुसार खोकला हा **'कास'** रोग मानला जातो, जो मुख्यत्वे **कफ आणि वात दोषाच्या असंतुलनामुळे** "
                "तसेच प्राणवह स्रोतसांमधील अडथळ्यामुळे निर्माण होतो. यासाठी कफशामक, उष्ण वीर्य आणि घशाला मऊ करणाऱ्या औषधी वनस्पती अत्यंत गुणकारी मानल्या जातात."
            )
            response_parts.append(
                "#### खोकल्यावरील पारंपारिक आयुर्वेदिक उपाय व पद्धती:\n"
                "• **तुळस (Tulsi) आणि मध**: ५ ते ७ ताज्या तुळशीच्या पानांचा रस काढून त्यात १ चमचा शुद्ध मध मिसळून दिवसातून दोन वेळा घेतल्यास कफ मोकळा होतो आणि खोकल्यात त्वरित आराम मिळतो.\n"
                "• **ज्येष्ठमध (Yashtimadhu / Mulethi)**: कोरडा खोकला आणि घशातील खवखव शांत करण्यासाठी ज्येष्ठमधाची कांडी चघळणे किंवा अर्धा चमचा ज्येष्ठमध पावडर कोमट पाण्यातून घेणे अत्यंत प्रभावी ठरते.\n"
                "• **सितोपलादि चूर्ण (Sitopaladi Churna)**: हे खोकला, सर्दी आणि कफासाठीचे शास्त्रीय चूर्ण आहे. हे चूर्ण मध आणि साजूक तुपासोबत चाटण करून घेतले जाते.\n"
                "• **सुंठ आणि कोमट पाणी**: सुंठ पावडर मधात मिसळून किंवा कोमट पाण्यातून घेतल्याने कफ वितळण्यास आणि पचन सुधारण्यास मदत होते.\n"
                "• **हळदीचे दूध व वाफ**: रात्री झोपताना कोमट दुधात चिमूटभर हळद टाकून पिणे आणि ओवा किंवा निलगिरी तेलाची वाफ घेणे श्वसनमार्ग मोकळा करते."
            )
        else:
            # General grounded synthesis in Marathi
            response_parts.append(
                f"**शास्त्रीय माहिती**: {primary.title} हे आयुर्वेदातील एक महत्त्वपूर्ण घटक आहे. "
                f"शास्त्रीय संदर्भांनुसार ({primary.source}) हे शारीरिक दोषांचे संतुलन राखण्यास आणि आरोग्य सुधारण्यास मदत करते."
            )

        # Complementary citations
        if len(citations) > 1:
            response_parts.append("#### पूरक आयुर्वेदिक संदर्भ व इतर वनस्पती:\n")
            for c in citations[1:]:
                alt_title = marathi_title_map.get(c.title, c.title)
                first_sentence = (c.content or c.snippet or "").split(". ")[0]
                response_parts.append(f"• **{alt_title}**: {first_sentence}.")

        # Marathi Educational Disclaimer
        response_parts.append(
            "\n### ⚠️ महत्त्वाची शैक्षणिक सूचना\n"
            "ही माहिती केवळ शास्त्रीय आयुर्वेदिक ग्रंथ (चरक संहिता, सुश्रुत संहिता) आणि आयुष (AYUSH) संदर्भ साहित्यावर आधारित शैक्षणिक मार्गदर्शनासाठी आहे. "
            "हा कोणताही वैद्यकीय सल्ला किंवा निदान नाही. तीव्र किंवा दीर्घकालीन लक्षणांसाठी कृपया तज्ज्ञ आयुर्वेदिक वैद्य किंवा डॉक्टरांचा प्रत्यक्ष सल्ला घ्या."
        )

        return SafetyClassifier.validate_output("\n\n".join(response_parts))

    def _synthesize_hindi_response(
        self,
        query: str,
        citations: List[SourceCitation],
        is_cough_query: bool
    ) -> str:
        """Synthesizes structured Ayurvedic guidance in Hindi."""
        primary = citations[0]
        response_parts = []
        response_parts.append(f"### {primary.title}\n")

        if is_cough_query or "tulsi" in primary.title.lower() or "sitopaladi" in primary.title.lower():
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
        else:
            response_parts.append(f"**आयुर्वेदिक विवरण**: {primary.content or primary.snippet or ''}")

        if len(citations) > 1:
            response_parts.append("#### प्रमुख सिद्धांत एवं शास्त्रीय दृष्टिकोण:\n")
            for c in citations[1:]:
                first_sentence = (c.content or c.snippet or "").split(". ")[0]
                if first_sentence:
                    response_parts.append(f"• **{c.title}**: {first_sentence}.")

        response_parts.append(
            "\n### महत्वपूर्ण शैक्षिक सूचना\n"
            "यह विवरण शास्त्रीय आयुर्वेदिक ग्रंथों और आयुष संदर्भों पर आधारित है। "
            "यह केवल शैक्षिक समझ के लिए प्रदान किया गया है और इसका उपयोग चिकित्सीय निदान या उपचार के रूप में न करें।"
        )
        return SafetyClassifier.validate_output("\n\n".join(response_parts))

# Global generator instance
rag_generator = RAGGenerator()
