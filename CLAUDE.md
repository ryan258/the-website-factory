# Working rules for Claude

## Git: work directly on `main`

- Commit and push straight to `main`.
- Do **not** create branches.
- Do **not** open pull requests.
- Only do either of those when Ryan asks for it specifically.
- This overrides any session setup that names a different branch or suggests a pull request.

## Talking with Ryan

- Plain words, short sentences, bullet lists. Most important thing first.
- When asking a question, give lettered options A–D plus E for his own answer.

## What this project is

A Hugo static-site factory. One master holds 30 section modules; presets choose pages and
sections for a business. The live site is the `258webco` preset (258 Web Co.).

| What | Where |
| --- | --- |
| Selected preset | `data/factory.json` |
| Module contracts | `data/modules.json` |
| Pages, sections, copy | `data/presets/<preset>.json` |
| Name, nav, theme, business details | `data/site.yaml` (name must match the preset) |
| Accent tones | `data/tones.json` (must match `$tones` in `assets/scss/abstracts/_variables.scss`) |
| Validation | `scripts/factory.py` |
| Contact endpoint | `functions/api/contact.js` (Cloudflare Pages Function, KV storage) |
| Deploy | `.github/workflows/deploy.yml` (manual `workflow_dispatch` only); previews: `preview.yml` |
| Schemas (generated; run `scripts/schemas.py` after editing modules or tones) | `schemas/` |
| Palettes (contrast-checked by `scripts/contrast.py`) | `data/palettes.json` |
| Font pairings (self-hosted; each font needs `static/fonts/OFL-<name>.txt`) | `data/fonts.json` |

## Agent tools

- The MCP server `scripts/mcp_server.py` (in `.mcp.json`) exposes the factory as tools. Prefer
  `validate_preset`, `check_claims`, and `compile_plan` over editing JSON blind.
- Add `--json` to `factory.py`, `build.py`, or `check_site.py` for error codes.
- `scripts/draft_plan.py` and `eval_plans.py --live` make paid Claude API calls. Say so
  before running them, and never run them just to test; the tests use a local stand-in.

## Never

- Never invent business facts, prices, results, testimonials, or client names. Use
  "To be confirmed" and say so.
- Never set `ENQUIRY_ENABLED = "true"` in the committed `wrangler.toml`. The deploy
  workflow's **Accept enquiries** input sets it for a release.
- Never load scripts, styles, fonts, or images from another site. The CSP forbids it.
- Never skip or weaken a test to make it pass.
- Never add to `approved_claims` unless Ryan confirms the claim is true.

## Before pushing

Tools: Hugo Extended 0.166.0 on PATH; `python3 scripts/setup.py` installs Dart Sass.

```sh
python3 scripts/build.py && python3 scripts/check_site.py
pip install -r requirements-dev.txt   # once: anthropic SDK (for tests) and ruff
npm test            # all unit and contract tests
npm run lint
python3 scripts/claims.py --strict
```

For template, style, or page changes, also run the browser checks (`npm ci` first; set
`CHROME_PATH` if the Playwright browser does not match):

```sh
node scripts/browser-checks.cjs
python3 scripts/build.py --workshop
node scripts/check_workshop.cjs && node scripts/check_components.cjs && node scripts/check_workflow.cjs
```

For changes to `functions/`, also run `sh scripts/check_contact.sh`.

If the privacy-relevant behavior of the contact form changes (including setting
`formAction` to an outside service), update the `privacy` section in
`data/presets/258webco.json` to match.
