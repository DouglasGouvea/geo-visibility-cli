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


# --------------------------------------------------------------------------
# Competitor candidates
# --------------------------------------------------------------------------

_CAPW = r"[A-ZÀ-Ý][\w&'’-]*"  # capitalized word; no dots, so a sentence end stops it
_CONN = r"(?:de|da|do|dos|das|di|von|van|of|&)"  # connectors allowed inside weak names
_CONN_ALL = r"(?:de|da|do|dos|das|di|von|van|of|e|and|&)"  # inside bold/heading/list names
_TITLEW = r"(?:Dr[a]?|Prof[a]?|Doutor[a]?)"
_TOKEN = rf"(?:{_CAPW}|\d[\w-]*)"

_SEQ_RE = re.compile(rf"{_CAPW}(?:[ \t]+(?:{_CONN}[ \t]+)?{_CAPW})*")
_NAMELIKE_RE = re.compile(
    rf"(?:{_TITLEW}\.?[ \t]+)?{_TOKEN}(?:[ \t]+(?:{_CONN_ALL}[ \t]+)?{_TOKEN})*"
)
_TITLE_RE = re.compile(
    rf"\b{_TITLEW}\.?[ \t]+{_CAPW}(?:[ \t]+(?:(?:de|da|do|dos|das|di|von|van)[ \t]+)?{_CAPW}){{0,3}}"
)
_SEQ_WORDS = rf"{_CAPW}(?:[ \t]+(?:{_CONN}[ \t]+)?{_CAPW})*"
_BIZ_PREFIX_RE = re.compile(
    r"\b(?:Cl[ií]nicas?|Odonto|Odontologia|Instituto|Centro|Studio|Est[uú]dio|Consult[oó]rio|"
    r"Hospital|Laborat[oó]rio|Escrit[oó]rio|Grupo|Clinic|Institute|Center|Centre|Group|"
    rf"Law[ \t]+(?:Firm|Offices?|Group)|Dental|Dentistry)[ \t]+{_SEQ_WORDS}"
)
_BIZ_SUFFIX_RE = re.compile(
    rf"{_CAPW}(?:[ \t]+(?:{_CONN}[ \t]+)?{_CAPW})*?[ \t]+"
    r"(?:Law[ \t]+Firm|Clinic|Dental|Dentistry|Advogados|Associados|Associates|Odontologia)\b"
)
_BOLD_RE = re.compile(r"\*\*([^*\n]{2,80}?)\*\*")
_LIST_RE = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
_HEAD_RE = re.compile(r"^\s*#{1,6}\s+")
_SEP_RE = re.compile(r"\s+[–—-]\s+|\s*:\s|\s*:$")
_LEAD_CUT_RE = re.compile(r"\s+[–—-]\s+|\s*:\s*|\s*\(")
_TITLE_PREFIX_RE = re.compile(r"^(?:dra?|drs?|profa?|doutora?)\.?\s+")
_HAS_TITLE_RE = re.compile(r"^(?:dra?|drs?|profa?|doutora?)\.?\s", re.I)

_CONNECT = {"de", "da", "do", "dos", "das", "di", "von", "van", "of", "e", "and"}

_STOP = {
    normalize(w)
    for w in (
        # articles, prepositions, conjunctions, pronouns (PT)
        "O Os A As Um Uma Uns Umas Em No Na Nos Nas Para Por Pelo Pela Com Sem Que Se Como "
        "Quando Onde Mas Ou E De Do Da Dos Das Ao Aos Isso Isto Esse Essa Esses Essas Este "
        "Esta Estes Estas Aquele Aquela Aqui Ali Lá Também Porém Contudo Todavia Portanto "
        "Assim Então Logo Pois Porque Embora Ainda Sempre Nunca Já Só Apenas Muito Muita "
        "Muitos Muitas Pouco Poucos Mais Menos Cada Todo Toda Todos Todas Outro Outra Outros "
        "Outras Alguns Algumas Algum Alguma Nenhum Nenhuma Qual Quais Quanto Quanta Quantos "
        "Você Voce Seu Sua Seus Suas Meu Minha Nosso Nossa Ele Ela Eles Elas Nós "
        # sentence openers / discourse (PT)
        "Não Nao Sim Antes Depois Durante Hoje Ontem Agora Caso Dependendo Geralmente "
        "Normalmente Lembre Lembrando Verifique Consulte Pesquise Procure Pergunte Escolha "
        "Considere Compare Veja Confira Peça Evite Prefira Busque Solicite Observe Fique "
        "Além Segundo Entre Dentre Sobre Após Perante Conforme Mediante Segue Seguem "
        "Importante Atenção Observação Nota Dica Dicas Exemplo Exemplos Resumo Conclusão "
        "Finais Final Principais Principal Melhores Melhor Opções Opção Recomendações "
        "Recomendação Considerações Contato Endereço Horário Horários Telefone Localização "
        "Especialidades Especialidade Serviços Serviço Site Registro Registros Fonte Fontes "
        "Preço Preços Valor Valores Avaliação Avaliações Custo Custos Faixa Média "
        # EN
        "The An In On At For To Of And Or But If When While With Without This That These "
        "Those It Its He She They We You I Here There However Also Some Many Most Other "
        "Another Several Each Every All Both Any Such Per Via From Into Over Under About "
        "Between Among Than Then Now Today Just Only Even Still Yes No Not Before After "
        "Always Never Check Consider Look Make Ask Keep Remember Ensure Verify Compare "
        "According Overall Additionally Furthermore Moreover Finally First Second Third "
        "Next Note Tip Tips Important Depending Generally Typically Usually Please Their "
        "Our Your My His Her Whether Since Because Although Though Unlike Like What Which "
        "Who Whom Whose How Can Do Does Is Are Was Were Be Been Based Summary Conclusion "
        "Verdict Overview Introduction Top Picks Pick Best Recommendations Recommendation "
        "Options Option Reviews Review Price Prices Cost Costs Rating Ratings Pros Cons "
        "FAQ Tips Steps Step Contact Address Hours Phone Location Services Service "
        # geography / web noise
        "Brazil Brasil Maps"
    ).split()
}

_GENERIC = {
    normalize(w)
    for w in (
        "clinica clinicas consultorio consultorios dentista dentistas odontologia odontologico "
        "odontologica odontologicos odonto medico medicos medica medicas advogado advogados "
        "advocacia escritorio escritorios centro centros instituto institutos studio estudio "
        "hospital hospitais laboratorio laboratorios grupo profissional profissionais "
        "especialista especialistas servico servicos saude clinic clinics dentist dentistry "
        "dental doctor doctors lawyer lawyers law firm firms center centre institute office "
        "offices group specialist specialists practice practices care health medical "
        "attorney attorneys associates associados"
    ).split()
}

_REGISTRY_ACR = {
    "cro", "crm", "oab", "crea", "crp", "cfm", "cfo", "crf", "crn", "cref", "creci", "coren",
    "cau", "crc", "cfc", "confea", "anvisa", "ans", "procon", "anatel", "inmetro", "sus",
    "cnpj", "cpf", "bbb", "fda", "ada", "ama", "aap", "aao", "aaoms", "nhs", "gdc", "cdc",
    "nih", "osha", "ftc", "abnt", "iso", "cda", "ahpra",
}
_REGISTRY_PHRASES = (
    "reclame aqui", "better business bureau", "conselho regional", "conselho federal",
    "ordem dos advogados", "american dental association", "american medical association",
    "food and drug administration", "ministerio da saude", "ministry of health",
)

_BUILTIN_PLATFORMS = {
    "doctoralia", "google", "yelp", "tripadvisor", "facebook", "instagram", "linkedin",
    "youtube", "wikipedia", "reclameaqui", "guiamais", "jusbrasil", "tiktok", "whatsapp",
    "reddit", "trustpilot", "glassdoor", "apontador", "solutudo", "telelistas", "waze",
    "healthgrades", "zocdoc", "webmd", "yellowpages", "angi", "avvo", "justia", "houzz",
    "thumbtack", "foursquare", "twitter", "pinterest", "quora", "ifood", "getninjas",
    "mercadolivre", "olx", "bing", "chatgpt", "perplexity", "gemini",
}
_TLDS = {
    "com", "org", "net", "co", "gov", "edu", "ac", "io", "app", "info", "biz", "med", "adv",
    "ind", "blog", "site", "online", "store", "br", "uk", "us",
}


def _stem(t: str) -> str:
    return t[:-1] if len(t) > 3 and t.endswith("s") else t


_GENERIC_STEMS = {_stem(g) for g in _GENERIC}


def _tokens(name: str) -> list[str]:
    """Normalized tokens of a name, without a leading Dr./Dra./Prof. title."""
    n = _TITLE_PREFIX_RE.sub("", normalize(name).strip())
    return re.findall(r"[a-z0-9]+(?:[-&'’][a-z0-9]+)*", n)


def _platform_label(entry: str) -> str:
    """'doctoralia.com.br' -> 'doctoralia'; 'Reclame Aqui' -> 'reclameaqui'."""
    e = entry.strip()
    if "." in e or "/" in e:
        parts = [p for p in domain_of(e).split(".") if p]
        while len(parts) > 1 and (parts[-1] in _TLDS or len(parts[-1]) == 2):
            parts.pop()
        return parts[-1].replace("-", "") if parts else ""
    return re.sub(r"[^a-z0-9]", "", normalize(e))


def _clean_candidate(name: str) -> str:
    name = name.strip(" .,:;-–—*_()[]\"'")
    words = name.split()
    while words and normalize(words[0].strip(".")) in _STOP:
        words.pop(0)
    while words and normalize(words[-1].strip(".")) in _STOP:
        words.pop()
    return " ".join(words)


def _name_like(s: str) -> bool:
    s = s.strip(" .,:;-–—*_()\"'")
    return bool(s) and len(s.split()) <= 7 and _NAMELIKE_RE.fullmatch(s) is not None


def _blank(s: str, a: int, b: int) -> str:
    return s[:a] + " " * (b - a) + s[b:]


def _take(rx: re.Pattern, body: str, out: list) -> str:
    """Record regex matches as strong candidates and blank them out of the line."""
    matches = list(rx.finditer(body))
    for m in matches:
        out.append((m.group(0), True, False))
    for m in matches:
        body = _blank(body, m.start(), m.end())
    return body


def _extract_line(line: str) -> list[tuple[str, bool, bool]]:
    """Return [(raw_name, strong, at_sentence_start)] for one line of an answer."""
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)  # markdown links
    line = re.sub(r"https?://\S+|\[\d+\]", " ", line)  # bare URLs, [1] citation marks
    out: list[tuple[str, bool, bool]] = []

    head = _HEAD_RE.match(line)
    lst = None if head else _LIST_RE.match(line)
    marker = head or lst
    body = " " * marker.end() + line[marker.end():] if marker else line

    # 1. bold spans
    bolds = list(_BOLD_RE.finditer(body))
    for m in bolds:
        lead = _LEAD_CUT_RE.split(m.group(1), 1)[0]
        if _name_like(lead):
            out.append((lead, True, False))
    for m in bolds:
        body = _blank(body, m.start(), m.end())
    body = body.replace("*", " ")

    # 2. heading text / list-item lead before dash or colon
    if marker:
        sep = _SEP_RE.search(body)
        lead_end = sep.start() if sep else (len(body) if head else 0)
        lead = re.sub(r"^\s*\d+[.)]\s*", "", body[:lead_end]).strip()
        if lead and _name_like(lead):
            words = lead.split()
            camel = len(words) == 1 and (
                re.search(r"[a-z][A-Z]", lead) or re.search(r"\d", lead)
            )
            strong = len(words) > 1 or bool(camel)
            out.append((lead, strong, not strong))
            body = _blank(body, 0, lead_end)

    # 3. titled people, 4. business patterns
    body = _take(_TITLE_RE, body, out)
    body = _take(_BIZ_PREFIX_RE, body, out)
    body = _take(_BIZ_SUFFIX_RE, body, out)

    # 5. remaining capitalized sequences (weak); never cross punctuation
    for m in _SEQ_RE.finditer(body):
        prev = body[: m.start()].rstrip(" \t\"'“‘([")
        at_start = not prev or prev[-1] in ".!?:;…"
        out.append((m.group(0), False, at_start))
    return out


def competitor_candidates(
    texts: list[str],
    brand: str,
    limit: int = 10,
    exclude: tuple[str, ...] = (),
    category: str = "",
    city: str = "",
    platforms: tuple[str, ...] | list[str] = (),
) -> list[tuple[str, int]]:
    """Heuristic competitor names found in answers, as (display name, answers).

    Prefers names with structure (bold, list leads, headings, Dr./Dra. titles,
    business patterns like "Clínica X"). Drops sentence-start words, generic
    category words, the city, the brand, registries (CRO, OAB, ...) and
    platforms (`platforms` = cited domains such as "doctoralia.com.br").
    Candidates are suggestions to review, not verified competitors.
    """
    per_text = [[o for line in t.splitlines() for o in _extract_line(line)] for t in texts]

    # words seen capitalized away from a sentence start (or in structure)
    mid_caps = {
        w for occs in per_text for raw, strong, at_start in occs
        if strong or not at_start for w in _tokens(raw)
    }

    brand_n = " ".join(_tokens(brand))
    city_tokens = set(_tokens(city))
    cat_stems = {_stem(t) for t in _tokens(category) if t not in _CONNECT}
    excl_keys = {" ".join(_tokens(e)) for e in (*exclude, city) if e}
    labels = set(_BUILTIN_PLATFORMS) | {_platform_label(p) for p in platforms if p}
    labels.discard("")

    def generic_like(t: str) -> bool:
        return (
            t in _STOP or t in _CONNECT or t in city_tokens
            or _stem(t) in _GENERIC_STEMS or _stem(t) in cat_stems
        )

    def is_junk(toks: list[str]) -> bool:
        core = [t for t in toks if t not in _CONNECT]
        key = " ".join(toks)
        if not core or len(key) < 3 or key.isdigit():
            return True
        if all(generic_like(t) for t in core):
            return True
        if brand_n and (brand_n in key or key in brand_n):
            return True
        if key in excl_keys:
            return True
        # registries / agencies (CRO-SP, OAB, Procon, Reclame Aqui, BBB...)
        if any(key.startswith(p) for p in _REGISTRY_PHRASES):
            return True
        reg = [t for t in core if re.split(r"[-/]", t)[0] in _REGISTRY_ACR]
        if reg and all(generic_like(t) for t in core if t not in reg):
            return True
        # platforms (cited domains and well-known sites)
        if "".join(core).replace("-", "") in labels:
            return True
        plat = [t for t in core if t.replace("-", "") in labels]
        if plat and all(generic_like(t) for t in core if t not in plat):
            return True
        return False

    counts: Counter[str] = Counter()
    forms: dict[str, Counter[str]] = {}
    strong_keys: set[str] = set()
    for occs in per_text:
        seen: set[str] = set()
        for raw, strong, at_start in occs:
            name = _clean_candidate(raw)
            toks = _tokens(name)
            if not toks or is_junk(toks):
                continue
            titled = bool(_HAS_TITLE_RE.match(name))
            if not strong and at_start and len(toks) == 1 and not titled and toks[0] not in mid_caps:
                continue
            key = " ".join(toks)
            forms.setdefault(key, Counter())[name] += 1
            if strong:
                strong_keys.add(key)
            seen.add(key)
        counts.update(seen)

    def best_form(key: str) -> str:
        def score(item: tuple[str, int]):
            f, freq = item
            accents = sum(1 for c in f if ord(c) > 127)
            return (bool(_HAS_TITLE_RE.match(f)), accents, len(f), freq)
        return max(forms[key].items(), key=score)[0]

    ranked = sorted(
        ((best_form(k), c, k in strong_keys) for k, c in counts.items()),
        key=lambda t: (-t[1], not t[2], t[0]),
    )
    return [(n, c) for n, c, _ in ranked[:limit]]
