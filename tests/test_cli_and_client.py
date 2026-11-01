import io
import json

import pytest

from geo_check import cli, perplexity
from geo_check.dryrun import simulate


def test_dry_run_end_to_end(tmp_path, capsys, monkeypatch):
    def no_net(*a, **k):
        raise AssertionError("network used in dry-run")

    monkeypatch.setattr("urllib.request.urlopen", no_net)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    rc = cli.main(
        [
            "dentista", "Campinas", "--brand", "Clinica Exemplo",
            "--site", "https://example.com", "--dry-run", "--out", str(tmp_path),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Relatório de Visibilidade GEO" in out  # "dentista" -> auto-detected PT
    assert "## O que isso significa" in out
    assert "fiverr.com/dougmanoel" in out and "geo-visibility-check.vercel.app" in out
    assert "GPTBot" in out
    json_path = next(tmp_path.glob("*.json"))
    assert str(json_path) in out
    assert list(tmp_path.glob("*.md"))
    data = json.loads(json_path.read_text())
    assert len(data["questions"]) == 5
    assert data["summary"]["total_answers"] == 15
    assert data["robots"]["crawlers"]["GPTBot"]["status"] == "blocked"


def test_dry_run_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        cli.main(["x", "y", "--brand", "Z", "--dry-run", "--out", str(d)])
    assert next(a.glob("*.json")).read_text() == next(b.glob("*.json")).read_text()
    assert simulate("q", "B", 0) == simulate("q", "B", 0)


def test_missing_key_clear_error(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    rc = cli.main(["x", "y", "--brand", "Z", "--out", str(tmp_path)])
    assert rc == 1
    assert "PERPLEXITY_API_KEY" in capsys.readouterr().err


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_perplexity_client_mocked(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["auth"] = req.get_header("Authorization")
        captured["body"] = json.loads(req.data)
        captured["ctype"] = req.get_header("Content-type")
        payload = {
            "output": [
                {
                    "type": "search_results",
                    "results": [
                        {"url": "https://s.com/1"},
                        {"url": "https://s.com/2"},
                        {"title": "no url"},
                    ],
                },
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Use Clinica Exemplo.",
                            "annotations": [
                                {"type": "url_citation", "url": "https://s.com/2"},
                                {"type": "url_citation", "url": "https://a.com/3"},
                                {"type": "other", "url": "https://ignored.com"},
                            ],
                        },
                        {"type": "output_text", "text": "Segunda parte."},
                    ],
                },
            ]
        }
        return FakeResp(json.dumps(payload).encode())

    monkeypatch.setattr(perplexity.urllib.request, "urlopen", fake_urlopen)
    res = perplexity.ask("pergunta?", "k123")
    assert res == {
        "answer": "Use Clinica Exemplo.\nSegunda parte.",
        "citations": ["https://s.com/1", "https://s.com/2", "https://a.com/3"],
    }
    assert captured["url"] == "https://api.perplexity.ai/v1/agent"
    assert captured["auth"] == "Bearer k123"
    assert captured["ctype"] == "application/json"
    assert captured["body"] == {"preset": "fast", "input": "pergunta?"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"output": "nope"},
        {"output": []},
        {"output": [{"type": "message", "content": []}]},
        {"output": [{"type": "search_results", "results": [{"url": "https://a.com"}]}]},
    ],
)
def test_perplexity_malformed_response(monkeypatch, payload):
    monkeypatch.setattr(
        perplexity.urllib.request, "urlopen",
        lambda req, timeout=None: FakeResp(json.dumps(payload).encode()),
    )
    with pytest.raises(perplexity.PerplexityError, match="Unexpected Perplexity response format"):
        perplexity.ask("q", "k")


def test_cli_real_path_uses_mocked_client(tmp_path, monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "k")
    monkeypatch.setattr(
        perplexity, "ask",
        lambda q, key: {"answer": "Clínica EXEMPLO é ótima", "citations": ["https://x.com/a"]},
    )
    rc = cli.main(["x", "y", "--brand", "Clinica Exemplo", "--runs", "2", "--out", str(tmp_path)])
    assert rc == 0
    data = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert data["summary"]["mention_rate"] == 1.0
    assert data["cited_domains"][0] == {"domain": "x.com", "count": 10}


def test_perplexity_http_error(monkeypatch):
    import urllib.error

    def boom(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 403, "no", {}, io.BytesIO(b"forbidden-body " + b"x" * 400)
        )

    monkeypatch.setattr(perplexity.urllib.request, "urlopen", boom)
    with pytest.raises(perplexity.PerplexityError, match="403: forbidden-body") as ei:
        perplexity.ask("q", "SECRETKEY")
    assert "SECRETKEY" not in str(ei.value)
    assert len(str(ei.value)) < 360
