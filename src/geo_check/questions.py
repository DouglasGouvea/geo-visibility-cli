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


def generate_questions(category: str, city: str, lang: str = "pt") -> list[str]:
    if lang not in TEMPLATES:
        raise ValueError(f"Unsupported language: {lang!r} (use 'pt' or 'en')")
    return [t.format(category=category, city=city) for t in TEMPLATES[lang]]
