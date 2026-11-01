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
| `--out DIR` | `./reports` | Where the `.json` and `.md` files go |
| `--dry-run` | off | Deterministic simulation, no network, no API key |
| `--version` | | Print the version and exit |

The Markdown report is printed to stdout and the JSON path is printed at the end.

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
| acheioprofissional | 9 |

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

Store the key as a repository secret (`PERPLEXITY_API_KEY`); it is read from the environment only. The action writes the `.json` and `.md` files to `./reports`, which the last step uploads.

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
- `--out DIR`: pasta dos arquivos `.json` e `.md` (padrão `./reports`).
- `--dry-run`: simula tudo, sem rede e sem chave. Bom para testar.
- O relatório em Markdown vai para a saída padrão.
- Só a Perplexity é consultada nesta versão. Os resultados variam entre execuções: é uma amostra, não um ranking.

Exemplo real (novembro de 2026): dentista em Campinas, marca OdontoCompany, 15 respostas, 0% de menção; a IA cita sobretudo doctoralia.com.br (96 citações). Veja a seção "Real example output".

## Full audit / Auditoria completa

- Full audit (ChatGPT, Gemini, Perplexity): https://www.fiverr.com/dougmanoel/audit-how-chatgpt-gemini-and-perplexity-mention-your-business
- Free checker: https://geo-visibility-check.vercel.app

## License

MIT, see [LICENSE](LICENSE).
