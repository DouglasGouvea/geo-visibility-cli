"""geo-check command line interface."""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

from . import __version__, dryrun, perplexity, robots
from .analysis import competitor_candidates, count_mentions, rank_domains
from .questions import detect_lang, generate_questions
from .report import render_markdown


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="geo-check",
        description="Check how AI answer engines mention your brand.",
    )
    p.add_argument("category", help='Business category, e.g. "dentista"')
    p.add_argument("city", help='City, e.g. "Campinas"')
    p.add_argument("--brand", required=True, help="Brand name to look for")
    p.add_argument("--site", help="Site URL; checks robots.txt for AI crawlers")
    p.add_argument(
        "--lang", choices=["pt", "en"], default=None,
        help="Language of questions and report (default: auto-detect from the category)",
    )
    p.add_argument("--runs", type=int, default=3, help="Runs per question (default 3)")
    p.add_argument("--out", default="./reports", help="Output directory (default ./reports)")
    p.add_argument("--dry-run", action="store_true", help="Simulate without any network")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def _slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "report"


def run_check(args) -> dict:
    args.lang = args.lang or detect_lang(args.category)
    questions = generate_questions(args.category, args.city, args.lang)
    api_key = None if args.dry_run else perplexity.get_api_key()

    q_results = []
    all_answers: list[str] = []
    all_citations: list[str] = []
    for q in questions:
        answers = []
        for i in range(args.runs):
            if args.dry_run:
                res = dryrun.simulate(q, args.brand, i)
            else:
                res = perplexity.ask(q, api_key)
            n = count_mentions(res["answer"], args.brand)
            answers.append({"run": i + 1, "mentions": n, **res})
            all_answers.append(res["answer"])
            all_citations += res["citations"]
        q_results.append(
            {
                "question": q,
                "mentions": sum(a["mentions"] for a in answers),
                "answers_with_mention": sum(1 for a in answers if a["mentions"] > 0),
                "answers": answers,
            }
        )

    total = len(all_answers)
    with_mention = sum(q["answers_with_mention"] for q in q_results)
    result = {
        "tool": f"geo-check {__version__}",
        "brand": args.brand,
        "category": args.category,
        "city": args.city,
        "lang": args.lang,
        "runs": args.runs,
        "engine": "simulated" if args.dry_run else f"perplexity/{perplexity.PRESET}",
        "dry_run": args.dry_run,
        "summary": {
            "total_answers": total,
            "answers_with_mention": with_mention,
            "mention_rate": (with_mention / total) if total else 0.0,
            "total_mentions": sum(q["mentions"] for q in q_results),
        },
        "questions": q_results,
        "cited_domains": [{"domain": d, "count": c} for d, c in rank_domains(all_citations)],
        "competitor_candidates": [
            {"name": n, "count": c}
            for n, c in competitor_candidates(
                all_answers,
                args.brand,
                category=args.category,
                city=args.city,
                platforms=[d for d, _ in rank_domains(all_citations)],
            )
        ],
        "site": args.site,
        "robots": None,
    }

    if args.site:
        if args.dry_run:
            result["robots"] = {
                "status": "ok",
                "simulated": True,
                "crawlers": robots.check_crawlers(robots.SIMULATED_ROBOTS),
            }
        else:
            f = robots.fetch_robots_status(args.site)
            rb = {"status": f["status"], "simulated": False, "code": f["code"], "error": None}
            if f["status"] == "ok":
                rb["crawlers"] = robots.check_crawlers(f["content"])
            elif f["status"] == "not_found":
                # no robots.txt: nothing is disallowed
                rb["crawlers"] = robots.check_crawlers("")
            else:
                rb["error"] = f["error"] or "unknown error"
            result["robots"] = rb
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.runs < 1:
        print("error: --runs must be >= 1", file=sys.stderr)
        return 2
    try:
        result = run_check(args)
    except perplexity.PerplexityError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    md = render_markdown(result)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"geo-{_slug(args.brand)}-{_slug(args.city)}"
    json_path = out_dir / f"{base}.json"
    md_path = out_dir / f"{base}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(md, encoding="utf-8")

    print(md)
    print(f"\nJSON: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
