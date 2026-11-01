# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-01

### Added
- Perplexity Agent API client (`/v1/agent`), replacing the previous endpoint.
- Report takeaways: a short, plain-language reading of the results at the top of the report.
- `--lang pt|en` to choose the language of questions and report (auto-detected from the category when omitted).
- `robots.txt` status in the report: distinguishes `ok`, `not_found` (nothing disallowed) and fetch errors, instead of silently treating failures as "allowed".
- PyPI packaging: SPDX license metadata, classifiers, project URLs, and a tag-triggered publish workflow using Trusted Publishing.
- `CHANGELOG.md`.

### Changed
- Better competitor extraction: filters out the brand itself, category and city words, and cited platforms. Candidates remain heuristic and should be reviewed manually.
- README rewritten with badges, real example output and a Portuguese section.
- Package version is read from `geo_check.__version__` (single source of truth).

[0.1.0]: https://github.com/DouglasGouvea/geo-visibility-cli/releases/tag/v0.1.0
