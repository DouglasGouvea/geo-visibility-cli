# geo-visibility-cli

[![CI](https://github.com/DouglasGouvea/geo-visibility-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/DouglasGouvea/geo-visibility-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/geo-visibility-cli.svg)](https://pypi.org/project/geo-visibility-cli/)

Check how AI answer engines mention your local business, and whether your site lets AI crawlers in.

`geo-check` asks buyer-style questions ("What is the best dentist in Campinas?") through the Perplexity API, several times each, then reports:

- how often your brand is mentioned (mention rate),
- which domains are cited most,
- candidate competitor names (**heuristic**, always review manually),
- plain-language takeaways,
- optionally, which AI crawlers your `robots.txt` allows or blocks (GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, Perplexity-User, ClaudeBot, Claude-Web, anthropic-ai, Google-Extended, CCBot, Bytespider, Applebot-Extended).

Only Perplexity is queried in this version. Results vary between runs; treat them as a sample, not a ranking.

## Install

From PyPI (once published):

```bash
pip install geo-visibility-cli
```

From source:

```bash
python3 -m venv .venv
.venv/bin/pip install -e . pytest
```

Requires Python >= 3.10, no runtime dependencies.

## Usage

```bash
export PERPLEXITY_API_KEY="..."   # from your Perplexity account; never commit it
geo-check "dentist" "Campinas" --brand "Clinica Exemplo" --site https://example.com --lang en
```

| Option | Default | Description |
|---|---|---|
| `category`, `city` | required | What you sell and where |
| `--brand` | required | Brand name (case/accent-insensitive match) |
| `--site URL` | none | Also check `robots.txt` for AI crawlers |
| `--lang pt\|en` | auto-detect from the category | Language of questions and report |
| `--runs N` | `3` | Times each question is asked |
| `--out DIR` | `./reports` | Where the report files go |
| `--format md\|html\|json` | `md` | `md`: Markdown + JSON files, report printed to stdout. `html`: single self-contained `.html` (inline CSS, no JavaScript) + JSON, paths printed. `json`: only the `.json` file, also printed to stdout |
| `--history-dir DIR` | none | Append each run to `DIR` and add a "Changes since last check" section |
| `--dry-run` | off | Deterministic simulation, no network, no API key |
| `--version` | | Print the version and exit |

The Markdown report is printed to stdout and the JSON path is printed at the end.

### History and changes

With `--history-dir geo-history`, every run writes a timestamped JSON record (brand, category, city, timestamp, mention rate, cited domains, competitors) to that folder. When an earlier run exists for the same brand/category/city, the report gets a **Changes since last check** section: mention-rate change in points, new/lost cited domains, new/lost competitor candidates. The HTML report also draws a bar chart of the mention rate over time. Works with `--dry-run` too.

```bash
geo-check "dentist" "Campinas" --brand "Clinica Exemplo" --history-dir geo-history --format html
```

Try it without a key:

```bash
geo-check "dentista" "Campinas" --brand "Clinica Exemplo" --dry-run
```

## Real example output

_Real run, November 2026._ Query: category `dentista`, city `Campinas`, brand `OdontoCompany`.

| Metric | Result |
|---|---|
| Answers collected | 15 |
| Mention rate | **0%** (0/15) |

Top cited domains:

| Domain | Citations |
|---|---|
| doctoralia.com.br | 96 |
| dentmap.com.br | 12 |
| acheioprofissional.com.br | 9 |

AI-recommended competitors (candidates, heuristic): Dra. Júlia Jacob, Dr. Sérgio Moura Guimarães, Dr. Guilherme Garcia.

Takeaway (as printed by the report, in Portuguese):

> **Invisível para a IA.** Nenhuma das 15 respostas citou OdontoCompany. Hoje, quem pergunta à IA por dentista em Campinas não é direcionado a você.

In short: the brand never appeared, and the AI answers lean heavily on one directory (doctoralia.com.br). A complete profile with recent reviews there is the first thing to fix.

> Competitor names come from a heuristic over the answer text. They can include false positives and miss real competitors; check them by hand before acting on them.

## GitHub Action

Run it on a schedule and keep the report as a build artifact:

```yaml
name: Weekly GEO check

on:
  schedule:
    - cron: "0 9 * * 1"   # every Monday, 09:00 UTC
  workflow_dispatch:

jobs:
  geo-check:
    runs-on: ubuntu-latest
    steps:
      - uses: DouglasGouvea/geo-visibility-cli@main
        with:
          category: dentist
          city: Campinas
          brand: Clinica Exemplo
          site: https://example.com
          dry-run: "false"
        env:
          PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
      - uses: actions/upload-artifact@v4
        with:
          name: geo-report
          path: reports/
```

Store the key as a repository secret (`PERPLEXITY_API_KEY`); it is read from the environment only. The action writes the report files to `./reports`, which the last step uploads.

| Input | Default | Description |
|---|---|---|
| `category`, `city`, `brand` | required | Same as the CLI |
| `site` | none | Check `robots.txt` for AI crawlers |
| `lang` | auto-detect | `pt` or `en` |
| `runs` | `3` | Runs per question |
| `history-dir` | none | Enables history and the "changes since last check" section |
| `format` | `md` | `md`, `html` or `json` |
| `dry-run` | `false` | Simulate without network or API key |

[`examples/weekly.yml`](examples/weekly.yml) is a ready-to-copy workflow: weekly cron plus manual trigger, `history-dir: geo-history`, `format: html`, and a final step that commits `geo-history/` and the latest report back to the repository (only when something changed). It needs `permissions: contents: write`.

## Tests

```bash
.venv/bin/python3 -m pytest -q
```

No test touches the network.

## Em português

`geo-check` mostra se a sua empresa aparece quando alguém pergunta a uma IA (hoje, a Perplexity) por um serviço na sua cidade, por exemplo "Qual o melhor dentista em Campinas?". Ele repete cada pergunta várias vezes e entrega:

- a **taxa de menção** da sua marca,
- os **domínios mais citados** pela IA (onde vale ter perfil e avaliações),
- **possíveis concorrentes** (heurística: confira manualmente),
- um resumo em linguagem simples do que isso significa,
- com `--site`, quais robôs de IA o seu `robots.txt` permite ou bloqueia.

Como usar:

```bash
pip install geo-visibility-cli     # ou: pip install -e . dentro do repositório
export PERPLEXITY_API_KEY="..."    # sua chave da Perplexity; nunca versione
geo-check "dentista" "Campinas" --brand "Clinica Exemplo" --site https://exemplo.com.br
```

- `--lang pt|en`: idioma das perguntas e do relatório (padrão: detectado pela categoria).
- `--runs N`: quantas vezes cada pergunta é feita (padrão 3).
- `--out DIR`: pasta dos arquivos do relatório (padrão `./reports`).
- `--format md|html|json`: formato do relatório (padrão `md`). `html` gera um único arquivo autônomo (CSS embutido, sem JavaScript); `json` grava só o `.json`.
- `--history-dir DIR`: guarda cada execução em `DIR` e acrescenta ao relatório a seção "Mudanças desde a última checagem" (variação da taxa de menção em pontos, domínios e concorrentes novos/perdidos) quando já existe uma execução anterior da mesma marca/categoria/cidade. No HTML, aparece também um gráfico de barras da taxa de menção ao longo do tempo. Funciona com `--dry-run`.
- `--dry-run`: simula tudo, sem rede e sem chave. Bom para testar.
- O relatório em Markdown vai para a saída padrão.
- GitHub Action: além de `category`, `city`, `brand`, `site` e `dry-run`, aceita `lang`, `runs`, `history-dir` e `format`. O exemplo [`examples/weekly.yml`](examples/weekly.yml) roda toda semana e grava o histórico (`geo-history/`) e o último relatório de volta no repositório.
- Só a Perplexity é consultada nesta versão. Os resultados variam entre execuções: é uma amostra, não um ranking.

Exemplo real (novembro de 2026): dentista em Campinas, marca OdontoCompany, 15 respostas, 0% de menção; a IA cita sobretudo doctoralia.com.br (96 citações). Veja a seção "Real example output".

## Full audit / Auditoria completa

- Product page / home: https://errandcode.com/geo
- Full audit on Fiverr (ChatGPT, Gemini, Perplexity): https://www.fiverr.com/dougmanoel/audit-how-chatgpt-gemini-and-perplexity-mention-your-business
- Free checker (same product): https://geo-visibility-check.vercel.app

## License

MIT, see [LICENSE](LICENSE).
