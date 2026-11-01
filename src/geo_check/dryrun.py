"""Deterministic simulated engine for --dry-run (no network)."""

import hashlib
import random

_COMPETITORS = [
    "Clínica Vida Plena",
    "Centro Médico Aurora",
    "Instituto Bem Estar",
    "Studio Prime",
    "Grupo Saúde Total",
    "Casa Modelo",
]
_DOMAINS = [
    "https://www.doctoralia.com.br/busca",
    "https://www.tripadvisor.com/list",
    "https://www.reclameaqui.com.br/empresa",
    "https://www.yelp.com/search",
    "https://pt.wikipedia.org/wiki/Guia",
    "https://www.guiamais.com.br/lista",
    "https://exemplo-blog.com.br/ranking",
]


def simulate(question: str, brand: str, run: int = 0) -> dict:
    """Return {'answer', 'citations'} deterministically from question + run."""
    seed = int.from_bytes(hashlib.sha256(f"{question}|{run}".encode()).digest()[:8], "big")
    rng = random.Random(seed)
    comps = rng.sample(_COMPETITORS, 3)
    lines = ["Here are some well-reviewed options:", ""]
    ranked = comps[:]
    if rng.random() < 0.45:
        ranked.insert(rng.randint(0, len(ranked)), brand)
    for i, name in enumerate(ranked, 1):
        lines.append(f"{i}. **{name}** - well reviewed locally.")
    answer = "\n".join(lines)
    citations = rng.sample(_DOMAINS, rng.randint(2, 4))
    return {"answer": answer, "citations": citations}
