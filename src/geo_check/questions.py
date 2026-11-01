"""Buyer-style question generation from PT and EN templates."""

TEMPLATES = {
    "pt": [
        "Qual o melhor {category} em {city}?",
        "Qual {category} em {city} tem as melhores avaliações?",
        "Você recomenda algum {category} em {city}? Quais as opções?",
        "Como escolher um bom {category} em {city}?",
        "Quanto custa um {category} em {city} e quem são os principais?",
    ],
    "en": [
        "What is the best {category} in {city}?",
        "Which are the top-rated {category} options in {city}?",
        "Can you recommend a {category} in {city}? What are the options?",
        "How do I choose a good {category} in {city}?",
        "How much does a {category} cost in {city} and who are the main ones?",
    ],
}


_PT_WORDS = {
    "dentista", "medico", "advogado", "restaurante", "academia", "pizzaria", "padaria",
    "farmacia", "psicologo", "veterinario", "contador", "arquiteto", "engenheiro",
    "eletricista", "encanador", "pediatra", "oftalmologista", "clinica", "escritorio",
    "loja", "salao", "barbearia", "mecanico", "oficina", "imobiliaria", "escola",
    "faculdade", "hotel", "pousada", "consultorio", "nutricionista", "fisioterapeuta",
}
_PT_SUFFIX = ("ista", "eiro", "eira", "aria", "ario", "orio", "ologo", "ador", "adora",
              "ncia", "dade", "cao", "sao")


def detect_lang(category: str, city: str = "") -> str:
    """'pt' if the category looks Portuguese (accents, common words, suffixes), else 'en'."""
    import unicodedata

    text = f"{category} {city}".strip()
    if any(c in text for c in "ãõçáéíóúâêôà"):
        return "pt"
    plain = "".join(
        c for c in unicodedata.normalize("NFKD", category.casefold()) if not unicodedata.combining(c)
    )
    for w in plain.split():
        if w in _PT_WORDS or (len(w) > 5 and w.endswith(_PT_SUFFIX)):
            return "pt"
    return "en"


def generate_questions(category: str, city: str, lang: str = "pt") -> list[str]:
    if lang not in TEMPLATES:
        raise ValueError(f"Unsupported language: {lang!r} (use 'pt' or 'en')")
    return [t.format(category=category, city=city) for t in TEMPLATES[lang]]
