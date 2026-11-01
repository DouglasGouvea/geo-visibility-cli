"""Markdown report rendering."""

FIVERR_URL = (
    "https://www.fiverr.com/dougmanoel/"
    "audit-how-chatgpt-gemini-and-perplexity-mention-your-business"
)
CHECKER_URL = "https://geo-visibility-check.vercel.app"

CTA = (
    "---\n\n"
    "**Want the full picture?** Get a full audit across ChatGPT, Gemini and Perplexity: "
    f"{FIVERR_URL}\n\n"
    f"Or try the free checker: {CHECKER_URL}\n"
)


def render_markdown(r: dict) -> str:
    s = r["summary"]
    out = [
        f"# GEO Visibility Report: {r['brand']}",
        "",
        f"- Category: {r['category']}",
        f"- City: {r['city']}",
        f"- Engine: {r['engine']}",
        f"- Runs per question: {r['runs']}",
        "",
        "## Summary",
        "",
        f"- Total answers: {s['total_answers']}",
        f"- Answers mentioning the brand: {s['answers_with_mention']}",
        f"- Mention rate: {s['mention_rate'] * 100:.0f}%",
        f"- Total brand mentions: {s['total_mentions']}",
        "",
        "## Questions",
        "",
        "| Question | Mentions | Answers with brand |",
        "|---|---|---|",
    ]
    for q in r["questions"]:
        out.append(f"| {q['question']} | {q['mentions']} | {q['answers_with_mention']}/{r['runs']} |")

    out += ["", "## Cited domains", ""]
    if r["cited_domains"]:
        out += ["| Domain | Citations |", "|---|---|"]
        out += [f"| {d['domain']} | {d['count']} |" for d in r["cited_domains"]]
    else:
        out.append("No citations returned.")

    out += ["", "## Competitor candidates (heuristic, review manually)", ""]
    if r["competitor_candidates"]:
        out += ["| Name | Answers |", "|---|---|"]
        out += [f"| {c['name']} | {c['count']} |" for c in r["competitor_candidates"]]
    else:
        out.append("None detected.")

    if r.get("robots") is not None:
        rb = r["robots"]
        out += ["", f"## AI crawler access ({r['site']})", ""]
        if rb.get("error"):
            out.append(f"Could not fetch robots.txt: {rb['error']}")
        else:
            if rb.get("simulated"):
                out.append("_Simulated robots.txt (dry-run)._\n")
            out += ["| Crawler | Status | Rule source |", "|---|---|---|"]
            out += [
                f"| {name} | {v['status']} | {v['source']} |"
                for name, v in rb["crawlers"].items()
            ]

    out += ["", CTA]
    return "\n".join(out)
