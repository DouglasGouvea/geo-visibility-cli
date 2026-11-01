"""Perplexity Agent API client (stdlib only)."""

import json
import os
import urllib.error
import urllib.request

API_URL = "https://api.perplexity.ai/v1/agent"
PRESET = "fast"


class PerplexityError(RuntimeError):
    pass


def get_api_key() -> str:
    key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not key:
        raise PerplexityError(
            "PERPLEXITY_API_KEY is not set. Export it in your environment "
            "(or use --dry-run to simulate without network)."
        )
    return key


def ask(question: str, api_key: str, timeout: int = 60) -> dict:
    """Ask one question. Returns {'answer': str, 'citations': [url, ...]}."""
    body = json.dumps({"preset": PRESET, "input": question}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            snippet = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            snippet = ""
        msg = f"Perplexity API returned HTTP {e.code}"
        if snippet:
            msg += f": {snippet}"
        raise PerplexityError(msg) from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise PerplexityError(f"Perplexity request failed: {e}") from e

    output = data.get("output") if isinstance(data, dict) else None
    if not isinstance(output, list):
        raise PerplexityError("Unexpected Perplexity response format")

    texts: list[str] = []
    citations: list[str] = []

    def add_url(url):
        if isinstance(url, str) and url and url not in citations:
            citations.append(url)

    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "search_results":
            for r in item.get("results") or []:
                if isinstance(r, dict):
                    add_url(r.get("url"))
        elif item.get("type") == "message":
            for part in item.get("content") or []:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                text = part.get("text")
                if isinstance(text, str) and text:
                    texts.append(text)
                for an in part.get("annotations") or []:
                    if isinstance(an, dict) and an.get("type") == "url_citation":
                        add_url(an.get("url"))

    if not texts:
        raise PerplexityError("Unexpected Perplexity response format")
    return {"answer": "\n".join(texts), "citations": citations}
