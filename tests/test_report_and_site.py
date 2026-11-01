import io
import json
import urllib.error

import pytest

from geo_check import cli, robots
from geo_check.questions import detect_lang
from geo_check.report import render_markdown, takeaways


def _result(rate_hits=0, total=10, lang="en", robots_=None, domains=None, site=None):
    return {
        "brand": "Acme", "category": "dentist", "city": "Boston", "lang": lang,
        "engine": "simulated", "runs": 2, "site": site, "robots": robots_,
        "summary": {
            "total_answers": total, "answers_with_mention": rate_hits,
            "mention_rate": rate_hits / total, "total_mentions": rate_hits,
        },
        "questions": [{"question": "q?", "mentions": rate_hits, "answers_with_mention": rate_hits}],
        "cited_domains": domains if domains is not None else [{"domain": "yelp.com", "count": 7}],
        "competitor_candidates": [{"name": "Smile Dental Group", "count": 3}],
    }


# ---------- language detection ----------

@pytest.mark.parametrize(
    "category,expected",
    [("dentista", "pt"), ("advogado trabalhista", "pt"), ("pizzaria", "pt"),
     ("médico", "pt"), ("nutricionista", "pt"), ("dentist", "en"),
     ("plumber", "en"), ("law firm", "en"), ("x", "en")],
)
def test_detect_lang(category, expected):
    assert detect_lang(category) == expected


# ---------- takeaways ----------

def test_zero_mentions_not_visible():
    tk = takeaways(_result(0))
    assert "Not visible to AI" in tk[0]
    pt = takeaways(_result(0, lang="pt"))
    assert "Invisível" in pt[0]


@pytest.mark.parametrize("hits,word", [(2, "Low"), (5, "Partial"), (9, "Strong")])
def test_rate_buckets(hits, word):
    assert word in takeaways(_result(hits))[0]


def test_top_platform_and_cap_of_three():
    rb = {"status": "ok", "crawlers": {"GPTBot": {"status": "blocked", "source": "specific"}}}
    tk = takeaways(_result(0, robots_=rb, domains=[{"domain": "yelp.com", "count": 7}], site="https://a.com"))
    assert len(tk) == 3
    assert "robots.txt" in tk[1] and "GPTBot" in tk[1]
    assert "yelp.com" in tk[2] and "7" in tk[2]


def test_platform_skips_own_site():
    domains = [{"domain": "a.com", "count": 9}, {"domain": "yelp.com", "count": 2}]
    tk = takeaways(_result(5, domains=domains, site="https://www.a.com"))
    assert any("yelp.com" in x for x in tk) and not any("a.com (" in x for x in tk)


def test_robots_missing_and_unreachable_notes():
    nf = {"status": "not_found", "code": 404, "crawlers": robots.check_crawlers("")}
    assert any("No robots.txt" in x for x in takeaways(_result(5, robots_=nf, site="https://a.com")))
    un = {"status": "unreachable", "error": "boom"}
    assert any("could not be checked" in x for x in takeaways(_result(5, robots_=un, site="https://a.com")))


# ---------- report rendering ----------

def test_report_en_and_pt_sections_and_cta_last():
    en = render_markdown(_result(5))
    assert "# GEO Visibility Report: Acme" in en and "## What this means" in en
    assert "## Cited domains" in en and "Smile Dental Group" in en
    assert en.rstrip().endswith("https://geo-visibility-check.vercel.app")
    assert "fiverr.com/dougmanoel" in en.split("## What this means")[1].split("---")[-1]

    pt = render_markdown(_result(5, lang="pt"))
    assert "# Relatório de Visibilidade GEO: Acme" in pt and "## O que isso significa" in pt
    assert "## Domínios citados" in pt and "Taxa de menção" in pt
    assert "## What this means" not in pt
    assert "fiverr.com/dougmanoel" in pt


# ---------- robots.txt: missing / unreachable (mocked HTTP) ----------

class FakeResp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _run(tmp_path, monkeypatch, urlopen, lang="en"):
    monkeypatch.setattr(robots.urllib.request, "urlopen", urlopen)
    monkeypatch.setenv("PERPLEXITY_API_KEY", "k")
    monkeypatch.setattr(
        cli.perplexity, "ask",
        lambda q, key: {"answer": "**Smile Dental Group** is great.", "citations": ["https://yelp.com/x"]},
    )
    rc = cli.main(
        ["dentist", "Boston", "--brand", "Acme", "--site", "https://a.com", "--runs", "1",
         "--lang", lang, "--out", str(tmp_path)]
    )
    assert rc == 0
    data = json.loads(next(tmp_path.glob("*.json")).read_text())
    md = next(tmp_path.glob("*.md")).read_text()
    return data, md


def _robots_section(md: str) -> str:
    return md.split("## AI crawler access")[1].split("---")[0]


def test_robots_404_shown_clearly(tmp_path, monkeypatch):
    def nf(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    data, md = _run(tmp_path, monkeypatch, nf)
    assert "robots.txt not found (404) - AI crawlers allowed by default" in md
    assert "None" not in _robots_section(md)
    assert data["robots"]["status"] == "not_found"
    assert data["robots"]["crawlers"]["GPTBot"]["status"] == "allowed"
    assert "No robots.txt found" in md  # takeaway


def test_robots_404_pt(tmp_path, monkeypatch):
    def nf(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    _, md = _run(tmp_path, monkeypatch, nf, lang="pt")
    assert "robots.txt não encontrado (404) - crawlers de IA permitidos por padrão" in md


@pytest.mark.parametrize(
    "exc",
    [urllib.error.URLError("Name or service not known"), TimeoutError("timed out"),
     ConnectionResetError("reset")],
)
def test_robots_unreachable_shown_clearly(tmp_path, monkeypatch, exc):
    def boom(req, timeout=None):
        raise exc

    data, md = _run(tmp_path, monkeypatch, boom)
    assert "Could not reach site:" in md
    assert "None" not in _robots_section(md)
    assert data["robots"]["status"] == "unreachable" and data["robots"]["error"]
    assert "crawlers" not in data["robots"]


def test_robots_http_500_not_none(tmp_path, monkeypatch):
    def err(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", {}, None)

    data, md = _run(tmp_path, monkeypatch, err)
    assert "robots.txt returned HTTP 503" in md and "None" not in _robots_section(md)
    assert data["robots"]["status"] == "http_error"


def test_robots_ok_mocked(tmp_path, monkeypatch):
    body = b"User-agent: GPTBot\nDisallow: /\n"
    data, md = _run(tmp_path, monkeypatch, lambda req, timeout=None: FakeResp(body))
    assert data["robots"]["crawlers"]["GPTBot"]["status"] == "blocked"
    assert "| GPTBot | blocked |" in md
    assert "Fix your robots.txt" in md


def test_fetch_robots_status_shapes(monkeypatch):
    monkeypatch.setattr(
        robots.urllib.request, "urlopen",
        lambda req, timeout=None: (_ for _ in ()).throw(ValueError("bad url")),
    )
    r = robots.fetch_robots_status("a.com")
    assert r["status"] == "unreachable" and r["error"] and r["content"] is None
    assert robots.fetch_robots("a.com") is None
