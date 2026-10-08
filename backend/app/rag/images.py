from typing import Optional, Dict, List, Any

HERB_IMAGES: Dict[str, Dict[str, str]] = {
    "tulsi": {
        "title": "Tulsi (Holy Basil) — Ocimum sanctum",
        "url": "/images/herbs/tulsi.jpg",
        "caption": "Fresh Holy Basil (Tulsi) with characteristic flowering blossoms and aromatic green leaves.",
        "botanical": "Ocimum sanctum (Lamiaceae)"
    },
    "ashwagandha": {
        "title": "Ashwagandha (Indian Ginseng) — Withania somnifera",
        "url": "/images/herbs/ashwagandha.jpg",
        "caption": "Ashwagandha plant with organic dried roots and red winter cherry berries.",
        "botanical": "Withania somnifera (Solanaceae)"
    },
    "triphala": {
        "title": "Triphala — The Classical Three-Fruit Synergy",
        "url": "/images/herbs/triphala.jpg",
        "caption": "The three classical fruits: Amalaki (Indian gooseberry), Haritaki, and Bibhitaki with churna.",
        "botanical": "Haritaki + Bibhitaki + Amalaki"
    },
    "amalaki": {
        "title": "Amalaki / Amla (Indian Gooseberry) — Phyllanthus emblica",
        "url": "/images/herbs/amla.jpg",
        "caption": "Fresh dewy green Indian Gooseberries (Amla) clustered on branch.",
        "botanical": "Phyllanthus emblica (Euphorbiaceae)"
    },
    "haridra": {
        "title": "Haridra / Turmeric — Curcuma longa",
        "url": "/images/herbs/turmeric.jpg",
        "caption": "Fresh golden turmeric rhizomes sliced with pure vibrant curcumin powder.",
        "botanical": "Curcuma longa (Zingiberaceae)"
    },
    "neem": {
        "title": "Neem (Nimba) — Azadirachta indica",
        "url": "/images/herbs/neem.jpg",
        "caption": "Fresh vibrant green Neem leaves and delicate white blossoms.",
        "botanical": "Azadirachta indica (Meliaceae)"
    },
    "ayurveda": {
        "title": "Classical Ayurveda — Science of Life",
        "url": "/images/herbs/ayurveda.jpg",
        "caption": "Traditional brass mortar and pestle with healing herbs, herbal oils, and Sanskrit manuscript.",
        "botanical": "Traditional Ayurvedic Formulations"
    }
}

IMAGE_INTENT_KEYWORDS = {
    "image", "images", "photo", "photos", "picture", "pictures", "pic", "pics",
    "look like", "looks like", "dikhao", "dikhao image", "photo dikhao", "tasveer",
    "kaisa dikhta hai", "kaisa hota hai", "kashi diste", "kasa disto", "chitra", "kashi aahe",
    "dakhva", "dakhva photo"
}

def detect_image_for_query(
    query: str,
    canonical_terms: Optional[List[str]] = None,
    fallback_herb: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Detects if an authentic botanical image matches the query or if the user asked to see a photo.
    Returns dict with title, url, caption, botanical name or None.
    """
    q_lower = query.lower()
    is_explicit = any(kw in q_lower for kw in IMAGE_INTENT_KEYWORDS)

    # Build search context from query and any resolved canonical terms
    check_pool = [q_lower]
    if canonical_terms:
        check_pool.extend([t.lower() for t in canonical_terms])
    combined = " ".join(check_pool)

    # Check specific herbs first
    for key, img_data in HERB_IMAGES.items():
        if key == "ayurveda":
            continue

        aliases = [key]
        if key == "tulsi":
            aliases.extend(["tulas", "holy basil", "तुळस", "तुलसी"])
        elif key == "ashwagandha":
            aliases.extend(["asgandh", "withania", "अश्वगंधा", "aswagandha"])
        elif key == "triphala":
            aliases.extend(["triphla", "three fruits", "त्रिफला", "trifala"])
        elif key == "amalaki":
            aliases.extend(["amla", "avla", "gooseberry", "आमलकी", "आवळा", "आंवला"])
        elif key == "haridra":
            aliases.extend(["turmeric", "haldi", "halad", "हल्दी", "हळद", "हरिद्रा"])
        elif key == "neem":
            aliases.extend(["nimba", "kadulimb", "नीम", "कडुलिंब"])

        if any(alias in combined for alias in aliases):
            return img_data

    # Check general Ayurveda or Tridosha
    if any(k in combined for k in ["ayurveda", "ayurvedic", "tridosha", "dosha", "auredik", "aurvedik"]):
        # Show image if explicitly requested or if asked about what is ayurveda / tridosha
        if is_explicit or any(k in combined for k in ["what is ayurveda", "tridosha", "origin"]):
            return HERB_IMAGES["ayurveda"]

    # If explicit image request without specific herb, show general Ayurveda
    if is_explicit:
        return HERB_IMAGES["ayurveda"]

    # Fallback herb if provided (e.g. from clinical consultation)
    if fallback_herb and fallback_herb in HERB_IMAGES:
        return HERB_IMAGES[fallback_herb]

    return None

