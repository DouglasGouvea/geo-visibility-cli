"""Self-contained HTML report (inline CSS, no JavaScript, inline SVG chart)."""

import re
from html import escape

from .history import CHART_MAX_POINTS
from .report import (
    CHECKER_URL, FIVERR_URL, T, _lang, changes_items, changes_rate_line, robots_view,
    takeaways,
)

ACCENT = "#2f5d8a"

CSS = f"""
:root {{ --accent: {ACCENT}; --ink: #222; --muted: #666; --line: #ddd; --bg: #fafafa; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); line-height: 1.5;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
main {{ max-width: 860px; margin: 0 auto; padding: 32px 20px 48px; background: #fff;
  border-left: 1px solid var(--line); border-right: 1px solid var(--line); }}
h1 {{ font-size: 1.6rem; margin: 0 0 8px; }}
h2 {{ font-size: 1.15rem; margin: 32px 0 8px; padding-bottom: 4px;
  border-bottom: 2px solid var(--accent); }}
ul {{ padding-left: 20px; }}
li {{ margin: 4px 0; }}
.meta {{ color: var(--muted); list-style: none; padding: 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.95rem; }}
th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--line); }}
th {{ background: #f0f0f0; font-weight: 600; }}
.rate {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
.note {{ color: var(--muted); font-style: italic; }}
footer {{ margin-top: 40px; padding: 16px; border: 1px solid var(--line); border-radius: 4px;
  background: var(--bg); }}
footer a {{ color: var(--accent); }}
svg text {{ font-family: inherit; }}
"""


def _e(x) -> str:
    return escape(str(x), quote=True)


def _rich(text: str) -> str:
    """Escape, then turn the **bold** markers used in the report strings into <strong>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _e(text))


def _table(headers: list[str], rows: list[list]) -> str:
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{_e(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _chart(history: list[dict], t: dict) -> str:
    pts = history[-CHART_MAX_POINTS:]
    bar_w, gap, h_plot, top, left = 36, 14, 120, 18, 36
    width = left + len(pts) * (bar_w + gap) + gap
    height = top + h_plot + 34
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{_e(t["history_alt"])}">',
        f"<title>{_e(t['history_alt'])}</title>",
    ]
    for pct in (0, 50, 100):
        y = top + h_plot - h_plot * pct / 100
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width}" y2="{y:.1f}" stroke="#ddd"/>'
            f'<text x="{left - 6}" y="{y + 4:.1f}" font-size="10" fill="#666" '
            f'text-anchor="end">{pct}%</text>'
        )
    for i, p in enumerate(pts):
        rate = max(0.0, min(1.0, float(p["mention_rate"])))
        bh = h_plot * rate
        x = left + gap + i * (bar_w + gap)
        y = top + h_plot - bh
        label = _e(str(p["timestamp"])[:10])
        parts.append(
            f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{bh:.1f}" fill="{ACCENT}">'
            f"<title>{label}: {rate * 100:.0f}%</title></rect>"
            f'<text x="{x + bar_w / 2}" y="{y - 4:.1f}" font-size="10" fill="#222" '
            f'text-anchor="middle">{rate * 100:.0f}%</text>'
            f'<text x="{x + bar_w / 2}" y="{top + h_plot + 14}" font-size="9" fill="#666" '
            f'text-anchor="middle">{label[5:]}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def render_html(r: dict) -> str:
    lang = _lang(r)
    t = T[lang]
    s = r["summary"]
    b = [f"<h1>{_e(t['title'].format(brand=r['brand']))}</h1>"]
    b.append(
        '<ul class="meta">'
        f"<li>{_e(t['category'])}: {_e(r['category'])}</li>"
        f"<li>{_e(t['city'])}: {_e(r['city'])}</li>"
        f"<li>{_e(t['engine'])}: {_e(r['engine'])}</li>"
        f"<li>{_e(t['runs'])}: {_e(r['runs'])}</li></ul>"
    )

    b.append(f"<h2>{_e(t['summary'])}</h2>")
    b.append(f'<p class="rate">{s["mention_rate"] * 100:.0f}%</p>')
    b.append(
        "<ul>"
        f"<li>{_e(t['total_answers'])}: {_e(s['total_answers'])}</li>"
        f"<li>{_e(t['answers_with_mention'])}: {_e(s['answers_with_mention'])}</li>"
        f"<li>{_e(t['mention_rate'])}: {s['mention_rate'] * 100:.0f}%</li>"
        f"<li>{_e(t['total_mentions'])}: {_e(s['total_mentions'])}</li></ul>"
    )

    b.append(f"<h2>{_e(t['meaning'])}</h2>")
    b.append("<ul>" + "".join(f"<li>{_rich(x)}</li>" for x in takeaways(r)) + "</ul>")

    ch = r.get("changes")
    if ch:
        b.append(f"<h2>{_e(t['changes'])}</h2><ul>")
        b.append(f"<li>{_e(changes_rate_line(ch, s['mention_rate'], t))}</li>")
        b.append(f"<li>{_e(t['ch_prev'].format(when=ch['previous_timestamp']))}</li>")
        for label, items in changes_items(ch, t):
            b.append(f"<li>{_e(label)}: {_e(', '.join(items) if items else t['ch_none'])}</li>")
        b.append("</ul>")

    hist = r.get("history")
    if hist:
        b.append(f"<h2>{_e(t['history'])}</h2>{_chart(hist, t)}")

    b.append(f"<h2>{_e(t['questions'])}</h2>")
    b.append(
        _table(
            t["q_cols"],
            [[i["question"], i["mentions"], f"{i['answers_with_mention']}/{r['runs']}"]
             for i in r["questions"]],
        )
    )

    b.append(f"<h2>{_e(t['cited'])}</h2>")
    if r["cited_domains"]:
        b.append(_table(t["d_cols"], [[x["domain"], x["count"]] for x in r["cited_domains"]]))
    else:
        b.append(f'<p class="note">{_e(t["no_citations"])}</p>')

    b.append(f"<h2>{_e(t['competitors'])}</h2>")
    if r["competitor_candidates"]:
        b.append(
            _table(t["c_cols"], [[x["name"], x["count"]] for x in r["competitor_candidates"]])
        )
    else:
        b.append(f'<p class="note">{_e(t["none_detected"])}</p>')

    if r.get("robots") is not None:
        v = robots_view(r, t)
        b.append(f"<h2>{_e(v['title'])}</h2>")
        if v["note"]:
            b.append(f"<p>{_e(v['note'])}</p>")
        else:
            if v["simulated"]:
                b.append(f'<p class="note">{_e(t["simulated"].strip("_"))}</p>')
            b.append(_table(t["r_cols"], [list(row) for row in v["rows"]]))

    b.append(
        "<footer>"
        f'<p>{_rich(t["cta_lead"])}</p>'
        f'<p>{_e(t["footer_full"])}: <a href="{_e(FIVERR_URL)}">{_e(FIVERR_URL)}</a></p>'
        f'<p>{_e(t["footer_free"])}: <a href="{_e(CHECKER_URL)}">{_e(CHECKER_URL)}</a></p>'
        "</footer>"
    )

    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{lang}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_e(t['title'].format(brand=r['brand']))}</title>"
        f"<style>{CSS}</style></head><body><main>"
        + "\n".join(b)
        + "</main></body></html>\n"
    )
