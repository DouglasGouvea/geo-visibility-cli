# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.2.2

- Point project Homepage and the README full-audit section at https://errandcode.com/geo (Fiverr and the free checker remain linked).

## [0.2.1] - 2026-11-01

### Fixed
- Removed an invalid PyPI classifier that blocked the upload.

## [0.2.0] - 2026-11-01

### Added
- `--history-dir DIR`: each run is appended as a timestamped JSON record; the report gains a "Changes since last check" section (mention-rate change in points, new/lost cited domains, new/lost competitors) when a previous run of the same brand/category/city exists. Works with `--dry-run`.
- `--format md|html|json`. The HTML report is a single self-contained file (inline CSS, no JavaScript, PT/EN), with an inline SVG bar chart of the mention rate over time when history is available.
- GitHub Action inputs `lang`, `runs`, `history-dir` and `format`.
- `examples/weekly.yml`: weekly workflow that commits `geo-history/` and the latest report back to the repository.

### Fixed
- The "get listed where AI looks" takeaway no longer calls a platform the "most cited source" (it could be wrong when a generic source such as Wikipedia was skipped); it now always says "most-cited listing/review platform".

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

[0.2.1]: https://github.com/DouglasGouvea/geo-visibility-cli/releases/tag/v0.2.1
[0.2.0]: https://github.com/DouglasGouvea/geo-visibility-cli/releases/tag/v0.2.0
[0.1.0]: https://github.com/DouglasGouvea/geo-visibility-cli/releases/tag/v0.1.0
