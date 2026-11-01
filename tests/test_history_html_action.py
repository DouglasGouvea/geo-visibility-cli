import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geo_check import cli, history
from geo_check.html_report import render_html
from geo_check.report import takeaways

ROOT = Path(__file__).resolve().parent.parent
BASE_ARGS = ["dentist", "Campinas", "--brand", "Clinica Exemplo", "--dry-run", "--lang", "en"]


@pytest.fixture
def clock(monkeypatch):
    state = {"t": datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)}

    def now():
        state["t"] += timedelta(days=7)
        return state["t"]

    monkeypatch.setattr(history, "_now", now)


def _run(tmp_path, *extra):
    rc = cli.main(
        [*BASE_ARGS, "--out", str(tmp_path / "out"), "--history-dir",
         str(tmp_path / "hist"), *extra]
    )
    assert rc == 0
    return json.loads(next((tmp_path / "out").glob("*.json")).read_text())


# ---- history -------------------------------------------------------------


def test_first_run_has_no_changes_section(tmp_path, clock, capsys):
    data = _run(tmp_path)
    assert data["changes"] is None
    assert len(data["history"]) == 1
    out = capsys.readouterr().out
    assert "Changes since last check" not in out
    assert len(list((tmp_path / "hist").glob("*.json"))) == 1


def test_second_run_reports_unchanged(tmp_path, clock, capsys):
    _run(tmp_path)
    capsys.readouterr()
    data = _run(tmp_path)
    out = capsys.readouterr().out
    assert "## Changes since last check" in out
    assert "unchanged" in out
    assert data["changes"]["mention_rate_delta_points"] == 0
    assert len(data["history"]) == 2
    assert len(list((tmp_path / "hist").glob("*.json"))) == 2


def test_second_run_reports_deltas(tmp_path, clock, capsys):
    _run(tmp_path)
    # doctor the previous record: lower rate, one extra domain and competitor, drop a real one
    rec_path = next((tmp_path / "hist").glob("*.json"))
    rec = json.loads(rec_path.read_text())
    cur_domain = rec["cited_domains"][0]["domain"]
    rec["mention_rate"] = 0.0
    rec["cited_domains"] = [{"domain": "old-source.example", "count": 3}] + rec["cited_domains"][1:]
    rec["competitor_candidates"] = [{"name": "Old Rival", "count": 2}]
    rec_path.write_text(json.dumps(rec))
    capsys.readouterr()

    data = _run(tmp_path)
    ch = data["changes"]
    assert ch["mention_rate_delta_points"] == round(data["summary"]["mention_rate"] * 100, 1)
    assert ch["mention_rate_delta_points"] > 0
    assert cur_domain in ch["new_cited_domains"]
    assert ch["lost_cited_domains"] == ["old-source.example"]
    assert "Old Rival" in ch["lost_competitors"]
    out = capsys.readouterr().out
    assert "Mention rate: 0% ->" in out and "points" in out
    assert "old-source.example" in out


def test_history_ignores_other_brand_and_bad_files(tmp_path, clock):
    hist = tmp_path / "hist"
    hist.mkdir()
    (hist / "garbage.json").write_text("{not json")
    (hist / "list.json").write_text("[]")
    cli.main(["dentist", "Campinas", "--brand", "Other", "--dry-run", "--lang", "en",
              "--out", str(tmp_path / "o1"), "--history-dir", str(hist)])
    data = _run(tmp_path)
    assert data["changes"] is None  # the "Other" brand run is not a predecessor


def test_history_match_is_case_and_accent_insensitive(tmp_path, clock):
    cli.main(["dentist", "São Paulo", "--brand", "Clínica X", "--dry-run", "--lang", "en",
              "--out", str(tmp_path / "o1"), "--history-dir", str(tmp_path / "h")])
    cli.main(["dentist", "sao paulo", "--brand", "clinica x", "--dry-run", "--lang", "en",
              "--out", str(tmp_path / "o2"), "--history-dir", str(tmp_path / "h")])
    last = json.loads(next((tmp_path / "o2").glob("*.json")).read_text())
    assert last["changes"] is not None


def test_dry_run_and_real_history_are_separate(tmp_path):
    hist = tmp_path / "h"
    base = {"brand": "B", "category": "c", "city": "x", "summary": {"mention_rate": 0.5}}
    history.save_record(hist, history.make_record({**base, "dry_run": True},
                                                  datetime(2026, 1, 1, tzinfo=timezone.utc)))
    assert len(history.load_records(hist, "B", "c", "x", dry_run=True)) == 1
    assert history.load_records(hist, "B", "c", "x", dry_run=False) == []
    # a real run does not see the dry-run record as predecessor
    res = {**base, "dry_run": False, "cited_domains": [], "competitor_candidates": []}
    history.prepare_run(res, hist)
    assert res["changes"] is None and len(res["history"]) == 1


@pytest.mark.parametrize("patch", [
    {"timestamp": 123},
    {"mention_rate": "0.5"},
    {"mention_rate": True},
    {"cited_domains": [{"count": 1}]},
    {"competitor_candidates": [{"count": 1}]},
    {"cited_domains": "oops"},
    {"brand": None},
])
def test_load_records_skips_malformed(tmp_path, patch):
    hist = tmp_path / "h"
    hist.mkdir()
    good = {"timestamp": "2026-01-01T00:00:00.000000Z", "brand": "B", "category": "c",
            "city": "x", "dry_run": False, "mention_rate": 0.5,
            "cited_domains": [], "competitor_candidates": []}
    (hist / "good.json").write_text(json.dumps(good))
    (hist / "bad.json").write_text(json.dumps({**good, **patch}))
    recs = history.load_records(hist, "B", "c", "x")
    assert [r["timestamp"] for r in recs] == [good["timestamp"]]


def test_history_not_saved_if_report_write_fails(tmp_path, clock, monkeypatch):
    from pathlib import Path as P
    real = P.write_text

    def boom(self, *a, **k):
        if self.suffix == ".md":
            raise OSError("disk full")
        return real(self, *a, **k)

    monkeypatch.setattr(P, "write_text", boom)
    with pytest.raises(OSError):
        cli.main([*BASE_ARGS, "--out", str(tmp_path / "out"), "--history-dir",
                  str(tmp_path / "hist")])
    assert not (tmp_path / "hist").exists() or not list((tmp_path / "hist").glob("*.json"))


def test_changes_section_in_portuguese(tmp_path, clock, capsys):
    args = ["dentista", "Campinas", "--brand", "Clinica Exemplo", "--dry-run",
            "--out", str(tmp_path / "o"), "--history-dir", str(tmp_path / "h")]
    cli.main(args)
    capsys.readouterr()
    cli.main(args)
    assert "## Mudanças desde a última checagem" in capsys.readouterr().out


# ---- wording -------------------------------------------------------------


def _result(lang, cited):
    return {
        "lang": lang, "brand": "B", "category": "c", "city": "x",
        "summary": {"total_answers": 3, "answers_with_mention": 0, "mention_rate": 0.0,
                    "total_mentions": 0},
        "cited_domains": cited, "site": None, "robots": None,
    }


@pytest.mark.parametrize("lang,phrase,banned", [
    ("en", "most-cited listing/review platform", "most cited source"),
    ("pt", "plataforma de cadastro/avaliações mais citada", "fonte mais citada"),
])
def test_platform_takeaway_wording(lang, phrase, banned):
    cited = [{"domain": "wikipedia.org", "count": 9}, {"domain": "doctoralia.com.br", "count": 4}]
    text = " ".join(takeaways(_result(lang, cited)))
    assert phrase in text and banned not in text and "doctoralia.com.br" in text


# ---- HTML ----------------------------------------------------------------


def _html_result(lang="en", **over):
    r = _result(lang, [{"domain": "a.example", "count": 2}])
    r.update(
        runs=3, engine="simulated", category="<b>cat</b>", city="Camp & inas",
        brand='<script>alert("x")</script>',
        questions=[{"question": "Q <i>1</i>?", "mentions": 0, "answers_with_mention": 0}],
        competitor_candidates=[{"name": "Rival <img src=x>", "count": 1}],
    )
    r.update(over)
    return r


def test_html_escapes_everything():
    html = render_html(_html_result())
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>cat</b>" not in html and "&lt;b&gt;cat&lt;/b&gt;" in html
    assert "Camp &amp; inas" in html
    assert "<img src=x>" not in html and "<i>1</i>" not in html


def test_html_is_self_contained_no_js():
    html = render_html(_html_result())
    assert html.startswith("<!DOCTYPE html>") and "<style>" in html
    assert "<script" not in html.replace("&lt;script", "")
    assert "http://" not in html.replace("http://www.w3.org/2000/svg", "")
    assert "gradient" not in html
    assert "fiverr.com/dougmanoel" in html and "geo-visibility-check.vercel.app" in html


def test_html_svg_only_with_history():
    assert "<svg" not in render_html(_html_result())
    hist = [{"timestamp": "2026-11-08T09:00:00.000000Z", "mention_rate": 0.2},
            {"timestamp": "2026-11-15T09:00:00.000000Z", "mention_rate": 0.6}]
    html = render_html(_html_result(history=hist))
    assert html.count("<svg") == 1 and html.count("<rect") == 2
    assert "Mention rate over time" in html


def test_html_changes_section_escaped():
    ch = {"previous_timestamp": "t0", "previous_mention_rate": 0.0,
          "mention_rate_delta_points": 20.0, "new_cited_domains": ["<x>.example"],
          "lost_cited_domains": [], "new_competitors": [], "lost_competitors": []}
    html = render_html(_html_result(changes=ch))
    assert "Changes since last check" in html and "&lt;x&gt;.example" in html


def test_html_language():
    en, pt = render_html(_html_result("en")), render_html(_html_result("pt"))
    assert '<html lang="en">' in en and "Summary" in en
    assert '<html lang="pt">' in pt and "Resumo" in pt and "Auditoria completa" in pt


def test_cli_format_html_and_json(tmp_path, capsys):
    out = tmp_path / "o"
    assert cli.main([*BASE_ARGS, "--out", str(out), "--format", "html"]) == 0
    files = {p.suffix for p in out.iterdir()}
    assert files == {".html", ".json"}
    assert "HTML:" in capsys.readouterr().out

    out2 = tmp_path / "o2"
    assert cli.main([*BASE_ARGS, "--out", str(out2), "--format", "json"]) == 0
    assert {p.suffix for p in out2.iterdir()} == {".json"}
    assert json.loads(capsys.readouterr().out)["brand"] == "Clinica Exemplo"


def test_cli_html_with_history_has_chart(tmp_path, clock):
    _run(tmp_path, "--format", "html")
    _run(tmp_path, "--format", "html")
    html = next((tmp_path / "out").glob("*.html")).read_text()
    assert html.count("<rect") == 2 and "Changes since last check" in html


# ---- action.yml / example ------------------------------------------------


def test_action_inputs_wired_to_cli():
    text = (ROOT / "action.yml").read_text()
    for name, env, flag in [
        ("lang", "INPUT_LANG", "--lang"),
        ("runs", "INPUT_RUNS", "--runs"),
        ("history-dir", "INPUT_HISTORY_DIR", "--history-dir"),
        ("format", "INPUT_FORMAT", "--format"),
    ]:
        assert re.search(rf"^  {name}:\n", text, re.M), name
        assert f"{env}: ${{{{ inputs.{name} }}}}" in text
        assert f'{flag} "${env}"' in text


def test_weekly_example():
    text = (ROOT / "examples" / "weekly.yml").read_text()
    assert "cron:" in text and "workflow_dispatch" in text
    assert "contents: write" in text
    assert "history-dir: geo-history" in text and "format: html" in text
    assert "git diff --cached --quiet" in text and "git push" in text
