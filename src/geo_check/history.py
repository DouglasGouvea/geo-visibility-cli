"""Run history: one JSON record per run, and deltas against the previous run."""

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

CHART_MAX_POINTS = 12


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.casefold()).strip()


def _key(brand: str, category: str, city: str) -> tuple[str, str, str]:
    return (_norm(brand), _norm(category), _norm(city))


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _norm(text)).strip("-") or "x"


def make_record(result: dict, when: datetime) -> dict:
    return {
        "timestamp": when.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "tool": result.get("tool"),
        "brand": result["brand"],
        "category": result["category"],
        "city": result["city"],
        "lang": result.get("lang"),
        "engine": result.get("engine"),
        "dry_run": result.get("dry_run", False),
        "mention_rate": result["summary"]["mention_rate"],
        "cited_domains": result.get("cited_domains", []),
        "competitor_candidates": result.get("competitor_candidates", []),
    }


def _valid_list(rec: dict, field: str, name_key: str) -> bool:
    items = rec.get(field)
    if items is None:
        return True
    return isinstance(items, list) and all(
        isinstance(x, dict) and isinstance(x.get(name_key), str) for x in items
    )


def _valid(rec: object) -> bool:
    if not isinstance(rec, dict):
        return False
    rate = rec.get("mention_rate")
    return (
        isinstance(rec.get("timestamp"), str)
        and isinstance(rate, (int, float))
        and not isinstance(rate, bool)
        and all(isinstance(rec.get(k), str) for k in ("brand", "category", "city"))
        and _valid_list(rec, "cited_domains", "domain")
        and _valid_list(rec, "competitor_candidates", "name")
    )


def load_records(
    history_dir: Path, brand: str, category: str, city: str, dry_run: bool = False
) -> list[dict]:
    """Records for the same brand/category/city and run kind (dry or real), oldest first.

    Bad files and malformed records are skipped.
    """
    want = _key(brand, category, city)
    out = []
    if not history_dir.is_dir():
        return out
    for p in history_dir.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (
            _valid(rec)
            and _key(rec["brand"], rec["category"], rec["city"]) == want
            and bool(rec.get("dry_run", False)) == bool(dry_run)
        ):
            out.append(rec)
    out.sort(key=lambda r: r["timestamp"])
    return out


def save_record(history_dir: Path, record: dict) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = re.sub(r"[^0-9TZ]", "", record["timestamp"])
    name = (
        f"{ts}-{_slug(record['brand'])}-{_slug(record['category'])}-{_slug(record['city'])}.json"
    )
    path = history_dir / name
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def compute_changes(prev: dict, record: dict) -> dict:
    """Deltas of the current record against the previous one."""

    def names(rec, field, name_key):
        return [x[name_key] for x in rec.get(field) or []]

    def diff(field, name_key):
        before, after = names(prev, field, name_key), names(record, field, name_key)
        return (
            [n for n in after if n not in before],
            [n for n in before if n not in after],
        )

    new_d, lost_d = diff("cited_domains", "domain")
    new_c, lost_c = diff("competitor_candidates", "name")
    return {
        "previous_timestamp": prev["timestamp"],
        "previous_mention_rate": prev["mention_rate"],
        "mention_rate_delta_points": round(
            (record["mention_rate"] - prev["mention_rate"]) * 100, 1
        ),
        "new_cited_domains": new_d,
        "lost_cited_domains": lost_d,
        "new_competitors": new_c,
        "lost_competitors": lost_c,
    }


def prepare_run(result: dict, history_dir: Path) -> dict:
    """Annotate `result` with `changes` and `history`; return the record to save later.

    Nothing is written here: call `save_record` once the reports are on disk.
    """
    prior = load_records(
        history_dir,
        result["brand"],
        result["category"],
        result["city"],
        bool(result.get("dry_run", False)),
    )
    record = make_record(result, _now())
    result["changes"] = compute_changes(prior[-1], record) if prior else None
    series = [{"timestamp": r["timestamp"], "mention_rate": r["mention_rate"]} for r in prior]
    series.append({"timestamp": record["timestamp"], "mention_rate": record["mention_rate"]})
    result["history"] = series
    return record


def record_run(result: dict, history_dir: Path) -> None:
    """Annotate `result` and append this run to the dir in one step."""
    save_record(history_dir, prepare_run(result, history_dir))
