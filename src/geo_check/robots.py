"""robots.txt analysis for AI crawlers."""

import urllib.error
import urllib.request
from urllib.parse import urlparse

AI_CRAWLERS = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "PerplexityBot",
    "Perplexity-User",
    "ClaudeBot",
    "Claude-Web",
    "anthropic-ai",
    "Google-Extended",
    "CCBot",
    "Bytespider",
    "Applebot-Extended",
]

# Simulated robots.txt used by --dry-run (no network).
SIMULATED_ROBOTS = """\
User-agent: GPTBot
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: Bytespider
Disallow: /

User-agent: *
Disallow: /admin/
"""


def parse_robots(content: str) -> list[dict]:
    """Parse robots.txt into groups: [{'agents': [lowercase UAs], 'rules': [(kind, path)]}]."""
    groups: list[dict] = []
    current: dict | None = None
    last_was_agent = False
    for raw in content.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            if current is None or not last_was_agent:
                current = {"agents": [], "rules": []}
                groups.append(current)
            current["agents"].append(value.lower())
            last_was_agent = True
        elif field in ("allow", "disallow"):
            last_was_agent = False
            if current is not None:
                current["rules"].append((field, value))
        else:
            last_was_agent = False
    return groups


def _rules_for(groups: list[dict], agent: str) -> tuple[list[tuple[str, str]], str]:
    a = agent.lower()
    specific = [r for g in groups if a in g["agents"] for r in g["rules"]]
    if any(a in g["agents"] for g in groups):
        return specific, "specific"
    wildcard = [r for g in groups if "*" in g["agents"] for r in g["rules"]]
    if any("*" in g["agents"] for g in groups):
        return wildcard, "wildcard"
    return [], "none"


def _root_allowed(rules: list[tuple[str, str]]) -> bool:
    """Longest-match wins for path '/', Allow wins ties; empty Disallow is ignored."""
    best_len, allowed = -1, True
    for kind, path in rules:
        if kind == "disallow" and path == "":
            continue
        if path and not ("/".startswith(path.rstrip("$").replace("*", ""))):
            continue
        plen = len(path)
        if plen > best_len or (plen == best_len and kind == "allow"):
            best_len, allowed = plen, kind == "allow"
    return allowed


def check_crawlers(content: str, crawlers: list[str] | None = None) -> dict[str, dict]:
    """Return {crawler: {'status': allowed|blocked|partial, 'source': specific|wildcard|none}}.

    'partial' = site root is allowed but some paths are disallowed.
    """
    groups = parse_robots(content)
    result = {}
    for agent in crawlers or AI_CRAWLERS:
        rules, source = _rules_for(groups, agent)
        if not _root_allowed(rules):
            status = "blocked"
        elif any(k == "disallow" and p not in ("", "/") for k, p in rules):
            status = "partial"
        else:
            status = "allowed"
        result[agent] = {"status": status, "source": source}
    return result


def fetch_robots_status(site: str, timeout: int = 10) -> dict:
    """Fetch robots.txt and say what happened.

    Returns {'status': 'ok'|'not_found'|'http_error'|'unreachable', 'content': str|None,
    'code': int|None, 'error': str|None}. 404/410 -> 'not_found' (no robots.txt means
    crawlers are allowed by default); other HTTP errors -> 'http_error'; network
    failures -> 'unreachable'.
    """
    if "//" not in site:
        site = "https://" + site
    p = urlparse(site)
    url = f"{p.scheme}://{p.netloc}/robots.txt"
    out = {"status": "ok", "content": None, "code": None, "error": None}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "geo-check/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out["content"] = resp.read().decode("utf-8", errors="replace")
            out["code"] = getattr(resp, "status", None)
    except urllib.error.HTTPError as e:
        out["code"] = e.code
        out["status"] = "not_found" if e.code in (404, 410) else "http_error"
        out["error"] = f"HTTP {e.code}"
    except (urllib.error.URLError, OSError, ValueError) as e:
        reason = getattr(e, "reason", None) or str(e) or type(e).__name__
        out["status"] = "unreachable"
        out["error"] = str(reason)
    return out


def fetch_robots(site: str, timeout: int = 10) -> str | None:
    """Fetch robots.txt content. Returns None if unreachable or missing."""
    return fetch_robots_status(site, timeout)["content"]
