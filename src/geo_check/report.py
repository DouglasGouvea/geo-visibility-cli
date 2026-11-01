"""Markdown report rendering (PT and EN)."""

from .analysis import domain_of

FIVERR_URL = (
    "https://www.fiverr.com/dougmanoel/"
    "audit-how-chatgpt-gemini-and-perplexity-mention-your-business"
)
CHECKER_URL = "https://geo-visibility-check.vercel.app"

# Generic sources that are not places a business can "get listed" (incl. subdomains)
_NON_LISTING = ("wikipedia.org", "youtube.com", "reddit.com")


def _is_listing_source(domain: str) -> bool:
    d = domain.lower()
    return not any(d == x or d.endswith("." + x) for x in _NON_LISTING)


LOW_RATE = 1 / 3
HIGH_RATE = 2 / 3

T = {
    "en": {
        "title": "GEO Visibility Report: {brand}",
        "category": "Category",
        "city": "City",
        "engine": "Engine",
        "runs": "Runs per question",
        "summary": "Summary",
        "total_answers": "Total answers",
        "answers_with_mention": "Answers mentioning the brand",
        "mention_rate": "Mention rate",
        "total_mentions": "Total brand mentions",
        "meaning": "What this means",
        "questions": "Questions",
        "q_cols": ["Question", "Mentions", "Answers with brand"],
        "cited": "Cited domains",
        "d_cols": ["Domain", "Citations"],
        "no_citations": "No citations returned.",
        "competitors": "Competitor candidates (heuristic, review manually)",
        "c_cols": ["Name", "Answers"],
        "none_detected": "None detected.",
        "robots": "AI crawler access ({site})",
        "r_cols": ["Crawler", "Status", "Rule source"],
        "simulated": "_Simulated robots.txt (dry-run)._",
        "rb_not_found": "robots.txt not found ({code}) - AI crawlers allowed by default.",
        "rb_unreachable": "Could not reach site: {error}",
        "rb_http_error": "robots.txt returned {error} - could not determine AI crawler rules.",
        "rb_generic_error": "Could not fetch robots.txt: {error}",
        "cta": (
            "**Want the full picture?** Get a full audit across ChatGPT, Gemini and "
            "Perplexity: {fiverr}\n\nOr try the free checker: {checker}\n"
        ),
        "changes": "Changes since last check",
        "ch_rate": "Mention rate: {prev}% -> {cur}% ({delta} points)",
        "ch_rate_same": "Mention rate: unchanged at {cur}%",
        "ch_prev": "Previous check: {when}",
        "ch_new_d": "New cited domains",
        "ch_lost_d": "Cited domains no longer present",
        "ch_new_c": "New competitor candidates",
        "ch_lost_c": "Competitor candidates no longer present",
        "ch_none": "None",
        "history": "Mention rate over time",
        "history_alt": "Bar chart of mention rate per check",
        "cta_lead": (
            "**Want the full picture?** Get a full audit across ChatGPT, Gemini and Perplexity."
        ),
        "footer_full": "Full audit",
        "footer_free": "Free checker",
        # takeaways
        "m_zero": (
            "**Not visible to AI.** None of the {total} answers mentioned {brand}. "
            "Today, people asking AI for a {category} in {city} are not being pointed to you."
        ),
        "m_low": (
            "**Low visibility.** {brand} appeared in only {pct}% of the answers. "
            "AI mentions you rarely, so most buyers asking AI will not see you."
        ),
        "m_mid": (
            "**Partial visibility.** {brand} appeared in {pct}% of the answers. "
            "You show up sometimes, but not reliably - there is room to grow."
        ),
        "m_high": (
            "**Strong visibility.** {brand} appeared in {pct}% of the answers. "
            "Keep your listings and reviews up to date to stay there."
        ),
        "platform": (
            "**Get listed where AI looks.** {domain} is the most-cited listing/review "
            "platform ({count} citations). Make sure {brand} has a complete profile and recent "
            "reviews there."
        ),
        "robots_blocked": (
            "**Fix your robots.txt.** It blocks AI crawlers ({names}). "
            "While blocked, those AI tools cannot read your site."
        ),
        "robots_missing": (
            "**No robots.txt found.** AI crawlers are allowed by default, so nothing is "
            "blocking you - but a robots.txt lets you control this explicitly."
        ),
        "robots_unknown": (
            "**robots.txt could not be checked.** Confirm your site is reachable and that "
            "it does not block AI crawlers."
        ),
    },
    "pt": {
        "title": "Relatório de Visibilidade GEO: {brand}",
        "category": "Categoria",
        "city": "Cidade",
        "engine": "Motor",
        "runs": "Execuções por pergunta",
        "summary": "Resumo",
        "total_answers": "Total de respostas",
        "answers_with_mention": "Respostas que citam a marca",
        "mention_rate": "Taxa de menção",
        "total_mentions": "Total de menções à marca",
        "meaning": "O que isso significa",
        "questions": "Perguntas",
        "q_cols": ["Pergunta", "Menções", "Respostas com a marca"],
        "cited": "Domínios citados",
        "d_cols": ["Domínio", "Citações"],
        "no_citations": "Nenhuma citação retornada.",
        "competitors": "Possíveis concorrentes (heurística, revise manualmente)",
        "c_cols": ["Nome", "Respostas"],
        "none_detected": "Nenhum detectado.",
        "robots": "Acesso de crawlers de IA ({site})",
        "r_cols": ["Crawler", "Status", "Origem da regra"],
        "simulated": "_robots.txt simulado (dry-run)._",
        "rb_not_found": (
            "robots.txt não encontrado ({code}) - crawlers de IA permitidos por padrão."
        ),
        "rb_unreachable": "Não foi possível acessar o site: {error}",
        "rb_http_error": (
            "robots.txt respondeu {error} - não foi possível determinar as regras para "
            "crawlers de IA."
        ),
        "rb_generic_error": "Não foi possível obter o robots.txt: {error}",
        "cta": (
            "**Quer o quadro completo?** Peça uma auditoria completa no ChatGPT, Gemini e "
            "Perplexity: {fiverr}\n\nOu use o verificador gratuito: {checker}\n"
        ),
        "changes": "Mudanças desde a última checagem",
        "ch_rate": "Taxa de menção: {prev}% -> {cur}% ({delta} pontos)",
        "ch_rate_same": "Taxa de menção: sem mudança, {cur}%",
        "ch_prev": "Checagem anterior: {when}",
        "ch_new_d": "Novos domínios citados",
        "ch_lost_d": "Domínios que deixaram de ser citados",
        "ch_new_c": "Novos possíveis concorrentes",
        "ch_lost_c": "Possíveis concorrentes que sumiram",
        "ch_none": "Nenhum",
        "history": "Taxa de menção ao longo do tempo",
        "history_alt": "Gráfico de barras da taxa de menção por checagem",
        "cta_lead": (
            "**Quer o quadro completo?** Peça uma auditoria completa no ChatGPT, Gemini e "
            "Perplexity."
        ),
        "footer_full": "Auditoria completa",
        "footer_free": "Verificador gratuito",
        "m_zero": (
            "**Invisível para a IA.** Nenhuma das {total} respostas citou {brand}. "
            "Hoje, quem pergunta à IA por {category} em {city} não é direcionado a você."
        ),
        "m_low": (
            "**Visibilidade baixa.** {brand} apareceu em apenas {pct}% das respostas. "
            "A IA cita você raramente, então a maioria dos clientes que perguntam a ela não vê você."
        ),
        "m_mid": (
            "**Visibilidade parcial.** {brand} apareceu em {pct}% das respostas. "
            "Você aparece às vezes, mas sem consistência - há espaço para crescer."
        ),
        "m_high": (
            "**Boa visibilidade.** {brand} apareceu em {pct}% das respostas. "
            "Mantenha cadastros e avaliações atualizados para continuar assim."
        ),
        "platform": (
            "**Esteja onde a IA procura.** {domain} é a plataforma de cadastro/avaliações "
            "mais citada ({count} citações). Garanta que {brand} tenha um perfil completo e avaliações "
            "recentes ali."
        ),
        "robots_blocked": (
            "**Corrija o seu robots.txt.** Ele bloqueia crawlers de IA ({names}). "
            "Enquanto estiver bloqueado, essas IAs não conseguem ler o seu site."
        ),
        "robots_missing": (
            "**Sem robots.txt.** Crawlers de IA são permitidos por padrão, então nada "
            "bloqueia você - mas um robots.txt permite controlar isso de forma explícita."
        ),
        "robots_unknown": (
            "**Não foi possível verificar o robots.txt.** Confirme que o site está no ar e "
            "que não bloqueia crawlers de IA."
        ),
    },
}


def _lang(r: dict) -> str:
    return r.get("lang") if r.get("lang") in T else "en"


def takeaways(r: dict) -> list[str]:
    """Up to 3 plain-language takeaways, chosen by rules (priority order)."""
    t = T[_lang(r)]
    s = r["summary"]
    ctx = {
        "brand": r["brand"], "category": r["category"], "city": r["city"],
        "total": s["total_answers"], "pct": f"{s['mention_rate'] * 100:.0f}",
    }
    out: list[str] = []

    rate = s["mention_rate"]
    if s["answers_with_mention"] == 0:
        out.append(t["m_zero"].format(**ctx))
    elif rate < LOW_RATE:
        out.append(t["m_low"].format(**ctx))
    elif rate < HIGH_RATE:
        out.append(t["m_mid"].format(**ctx))
    else:
        out.append(t["m_high"].format(**ctx))

    rb = r.get("robots")
    blocked = []
    if rb and rb.get("crawlers"):
        blocked = [n for n, v in rb["crawlers"].items() if v["status"] == "blocked"]
    if blocked:
        out.append(t["robots_blocked"].format(names=", ".join(blocked)))

    own = domain_of(r["site"]) if r.get("site") else ""
    for d in r.get("cited_domains") or []:
        if d["domain"] != own and _is_listing_source(d["domain"]):
            out.append(t["platform"].format(domain=d["domain"], count=d["count"], **ctx))
            break

    if rb and not blocked:
        if rb.get("status") == "not_found":
            out.append(t["robots_missing"])
        elif rb.get("error"):
            out.append(t["robots_unknown"])
    return out[:3]


def robots_view(r: dict, t: dict) -> dict:
    """Language-resolved robots content shared by the Markdown and HTML renderers."""
    rb = r["robots"]
    view = {"title": t["robots"].format(site=r["site"]), "note": None, "rows": None,
            "simulated": False}
    status = rb.get("status", "ok")
    if status == "unreachable":
        view["note"] = t["rb_unreachable"].format(error=rb.get("error") or "?")
    elif status == "http_error":
        view["note"] = t["rb_http_error"].format(error=rb.get("error") or "HTTP error")
    elif rb.get("error"):  # older/other shape
        view["note"] = t["rb_generic_error"].format(error=rb["error"])
    elif status == "not_found":
        view["note"] = t["rb_not_found"].format(code=rb.get("code") or 404)
    else:
        view["simulated"] = bool(rb.get("simulated"))
        view["rows"] = [(n, v["status"], v["source"]) for n, v in rb["crawlers"].items()]
    return view


def _robots_section(r: dict, t: dict) -> list[str]:
    v = robots_view(r, t)
    out = ["", f"## {v['title']}", ""]
    if v["note"]:
        out.append(v["note"])
        return out
    if v["simulated"]:
        out.append(t["simulated"] + "\n")
    h = t["r_cols"]
    out += [f"| {h[0]} | {h[1]} | {h[2]} |", "|---|---|---|"]
    out += [f"| {n} | {st} | {src} |" for n, st, src in v["rows"]]
    return out


def changes_rate_line(ch: dict, cur_rate: float, t: dict) -> str:
    ctx = {"prev": f"{ch['previous_mention_rate'] * 100:.0f}", "cur": f"{cur_rate * 100:.0f}"}
    delta = ch["mention_rate_delta_points"]
    if delta == 0:
        return t["ch_rate_same"].format(**ctx)
    return t["ch_rate"].format(delta=f"{delta:+g}", **ctx)


def changes_items(ch: dict, t: dict) -> list[tuple[str, list[str]]]:
    return [
        (t["ch_new_d"], ch["new_cited_domains"]),
        (t["ch_lost_d"], ch["lost_cited_domains"]),
        (t["ch_new_c"], ch["new_competitors"]),
        (t["ch_lost_c"], ch["lost_competitors"]),
    ]


def render_markdown(r: dict) -> str:
    t = T[_lang(r)]
    s = r["summary"]
    out = [
        f"# {t['title'].format(brand=r['brand'])}",
        "",
        f"- {t['category']}: {r['category']}",
        f"- {t['city']}: {r['city']}",
        f"- {t['engine']}: {r['engine']}",
        f"- {t['runs']}: {r['runs']}",
        "",
        f"## {t['summary']}",
        "",
        f"- {t['total_answers']}: {s['total_answers']}",
        f"- {t['answers_with_mention']}: {s['answers_with_mention']}",
        f"- {t['mention_rate']}: {s['mention_rate'] * 100:.0f}%",
        f"- {t['total_mentions']}: {s['total_mentions']}",
        "",
        f"## {t['meaning']}",
        "",
    ]
    out += [f"- {line}" for line in takeaways(r)]

    ch = r.get("changes")
    if ch:
        out += ["", f"## {t['changes']}", ""]
        out.append(f"- {changes_rate_line(ch, s['mention_rate'], t)}")
        out.append(f"- {t['ch_prev'].format(when=ch['previous_timestamp'])}")
        for label, items in changes_items(ch, t):
            out.append(f"- {label}: {', '.join(items) if items else t['ch_none']}")

    q = t["q_cols"]
    out += ["", f"## {t['questions']}", "", f"| {q[0]} | {q[1]} | {q[2]} |", "|---|---|---|"]
    for item in r["questions"]:
        out.append(
            f"| {item['question']} | {item['mentions']} | "
            f"{item['answers_with_mention']}/{r['runs']} |"
        )

    d = t["d_cols"]
    out += ["", f"## {t['cited']}", ""]
    if r["cited_domains"]:
        out += [f"| {d[0]} | {d[1]} |", "|---|---|"]
        out += [f"| {x['domain']} | {x['count']} |" for x in r["cited_domains"]]
    else:
        out.append(t["no_citations"])

    c = t["c_cols"]
    out += ["", f"## {t['competitors']}", ""]
    if r["competitor_candidates"]:
        out += [f"| {c[0]} | {c[1]} |", "|---|---|"]
        out += [f"| {x['name']} | {x['count']} |" for x in r["competitor_candidates"]]
    else:
        out.append(t["none_detected"])

    if r.get("robots") is not None:
        out += _robots_section(r, t)

    out += [
        "",
        "---",
        "",
        t["cta"].format(fiverr=FIVERR_URL, checker=CHECKER_URL),
    ]
    return "\n".join(out)
