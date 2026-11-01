# geo-visibility-cli

Check how AI answer engines mention your local business, and whether your site lets AI crawlers in.

`geo-check` asks buyer-style questions ("What is the best dentist in Campinas?") through the Perplexity API, several times each, then reports:

- how often your brand is mentioned (mention rate),
- which domains are cited most,
- candidate competitor names (heuristic, review manually),
- optionally, which AI crawlers your `robots.txt` allows or blocks (GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, Perplexity-User, ClaudeBot, Claude-Web, anthropic-ai, Google-Extended, CCBot, Bytespider, Applebot-Extended).

Only Perplexity is queried in this version. Results vary between runs; treat them as a sample, not a ranking.

## Install

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
| `--lang pt\|en` | `pt` | Question language |
| `--runs N` | `3` | Times each question is asked |
| `--out DIR` | `./reports` | Where the `.json` and `.md` files go |
| `--dry-run` | off | Deterministic simulation, no network, no API key |

The Markdown report is printed to stdout and the JSON path is printed at the end.

Try it without a key:

```bash
geo-check "dentista" "Campinas" --brand "Clinica Exemplo" --dry-run
```

## GitHub Action

```yaml
- uses: DouglasGouvea/geo-visibility-cli@main
  with:
    category: dentist
    city: Campinas
    brand: Clinica Exemplo
    site: https://example.com
    dry-run: "false"
  env:
    PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
```

Store the key as a repository secret; it is read from the environment only.

## Tests

```bash
.venv/bin/python3 -m pytest -q
```

No test touches the network.

## Português

`geo-check` faz perguntas de comprador ("Qual o melhor dentista em Campinas?") à API da Perplexity, várias vezes, e mostra a taxa de menção da sua marca, os domínios mais citados, possíveis concorrentes (heurística, confira manualmente) e, com `--site`, quais robôs de IA o seu `robots.txt` permite ou bloqueia.

```bash
export PERPLEXITY_API_KEY="..."
geo-check "dentista" "Campinas" --brand "Clinica Exemplo" --site https://exemplo.com.br
```

- `--lang pt|en` (padrão `pt`), `--runs` (padrão 3), `--out` (padrão `./reports`).
- `--dry-run` simula tudo sem rede e sem chave, útil para testar.
- O relatório em Markdown vai para a saída padrão; os arquivos `.json` e `.md` ficam em `--out`.
- Só a Perplexity é consultada nesta versão. Os resultados variam entre execuções.

## Full audit / Auditoria completa

- Full audit (ChatGPT, Gemini, Perplexity): https://www.fiverr.com/dougmanoel/audit-how-chatgpt-gemini-and-perplexity-mention-your-business
- Free checker: https://geo-visibility-check.vercel.app

## License

MIT, see [LICENSE](LICENSE).
