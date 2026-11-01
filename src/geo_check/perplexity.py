"""Perplexity API client (stdlib only)."""

import json
import os
import urllib.error
import urllib.request

API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar"


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
    body = json.dumps(
        {"model": MODEL, "messages": [{"role": "user", "content": question}]}
    ).encode("utf-8")
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
        raise PerplexityError(f"Perplexity API returned HTTP {e.code}") from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise PerplexityError(f"Perplexity request failed: {e}") from e

    try:
        answer = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as e:
        raise PerplexityError("Unexpected Perplexity response format") from e

    citations = list(data.get("citations") or [])
    for r in data.get("search_results") or []:
        url = r.get("url") if isinstance(r, dict) else None
        if url and url not in citations:
            citations.append(url)
    return {"answer": answer, "citations": citations}
