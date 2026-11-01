"""Answer analysis: brand mentions, cited domains, competitor candidates."""

import re
import unicodedata
from collections import Counter
from urllib.parse import urlparse


def normalize(text: str) -> str:
    """Lowercase and strip accents."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


def count_mentions(text: str, brand: str) -> int:
    """Count case/accent-insensitive occurrences of brand as a whole phrase."""
    b = normalize(brand).strip()
    if not b:
        return 0
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(p) for p in b.split()) + r"(?!\w)"
    return len(re.findall(pattern, normalize(text)))


def domain_of(url: str) -> str:
    host = urlparse(url if "//" in url else "//" + url).netloc.lower()
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def rank_domains(urls: list[str]) -> list[tuple[str, int]]:
    counts = Counter(d for d in (domain_of(u) for u in urls) if d)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


_CAP = r"[A-ZÀ-Ý][\w&'’.-]*"
_NAME_RE = re.compile(rf"{_CAP}(?:\s+(?:de|da|do|dos|das|e|&|of|and|the)?\s*{_CAP})*")
_BOLD_RE = re.compile(r"\*\*([^*\n]{2,60})\*\*")

_STOP = {
    normalize(w)
    for w in (
        "The A An In On At For To Of And Or But If When While With Without This That These Those "
        "It Its He She They We You I Here There However Also Some Many Most Other Another "
        "O Os As Um Uma Uns Umas Em No Na Nos Nas Para Por Com Sem Que Se Como Quando Onde "
        "Mas Ou E De Do Da Dos Das Ao Aos Isso Isto Esse Essa Este Esta Aqui Ali Também Porém "
        "Além Segundo Segundo Dentre Entre Veja Confira Atenção Observação Nota Note Tip Dica "
        "Brazil Brasil Google Maps Yelp Instagram Facebook Preço Preços Valor Valores Avaliação "
        "Avaliações Reviews Review Price Prices Cost Costs Rating Ratings Options Opções Opção "
        "Qual Quais Quanto Quanta Você Voce What Which How Can Do Does Is Are "
        "Resumo Summary Conclusion Conclusão Em Resumo Based Based On Baseado"
    ).split()
}


def _clean_candidate(name: str) -> str:
    name = name.strip(" .,:;-–—*_()[]\"'")
    words = name.split()
    while words and normalize(words[0]) in _STOP:
        words.pop(0)
    while words and normalize(words[-1]) in _STOP:
        words.pop()
    return " ".join(words)


def competitor_candidates(
    texts: list[str],
    brand: str,
    limit: int = 10,
    exclude: tuple[str, ...] = (),
) -> list[tuple[str, int]]:
    """Heuristic: bold names and capitalized phrases, excluding the brand.

    `exclude` lists extra terms to ignore (e.g. the city). Candidates are
    suggestions to review, not verified competitors.
    """
    brand_n = normalize(brand)
    excluded = {normalize(e) for e in exclude if e}
    counts: Counter[str] = Counter()
    for text in texts:
        found: list[str] = []
        found += _BOLD_RE.findall(text)
        found += _NAME_RE.findall(text)
        seen_in_text = set()
        for raw in found:
            name = _clean_candidate(raw)
            n = normalize(name)
            if len(n) < 3 or n in _STOP or n in excluded or n.isdigit():
                continue
            if brand_n and (brand_n in n or n in brand_n):
                continue
            seen_in_text.add(name)
        counts.update(seen_in_text)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:limit]
