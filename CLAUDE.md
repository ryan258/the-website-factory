# Working rules for Claude

## Git: work directly on `main`

- **Never run `git add`, `git commit`, or `git push` unless Ryan explicitly says so.** Any command or tool that stages, commits, or pushes counts, including `git commit -a`.
- "Explicitly" means he names the action in his message ("commit this", "push it"). Finishing a task, passing tests, or "go ahead" is not permission.
- Permission covers only the action he named. "Commit" does not mean "push", and it does not carry over to the next task.
- When he does say so, work directly on `main`: commit and push straight to `main`.
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
npm run verify     # the fast gates on a clean copy, as CI sees them (catches tests that need ignored files)
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

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **the-website-factory** (1388 symbols, 3334 relationships, 102 execution flows).

> Index stale? Run `node .gitnexus/run.cjs analyze --index-only` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? Bootstrap with `npx`, `bunx`, or `pnpm dlx` — e.g. `bunx gitnexus@latest analyze` (npm 11 npx crash; #1939).

## Always Do

- **MUST run impact before editing.** Use `impact({target: "symbolName", direction: "upstream"})` or `node .gitnexus/run.cjs impact "symbolName" --direction upstream --repo .`; report callers, processes, and risk. Never substitute grep for graph analysis.
- **MUST analyze graph changes before committing.** Use `detect_changes({scope: "all"})` (MCP) or `node .gitnexus/run.cjs detect-changes --scope all --repo .` (CLI fallback). `partial: true` or `truncated: true` is not a clean check — a zero means unseen, not unaffected; re-run it. For regression review: `detect_changes({scope: "compare", base_ref: "main"})` or `node .gitnexus/run.cjs detect-changes --scope compare --base-ref "main" --repo .`.
- MUST warn on HIGH/CRITICAL `risk` pre-edit; never use `riskSharedAxes` to waive a HIGH/CRITICAL `risk` warning. Compare File/symbol: MCP File omits axes; Graph-RAG expands File.
- **MUST treat `risk: UNKNOWN` as unresolved, not as low.** An empty caller set is not evidence the symbol is unused — it can also mean the callers are not resolvable by the index (plain-object property access, dynamic dispatch, cross-language calls). `impact` pairs `UNKNOWN` with a `riskNote` saying so. Confirm with a text search before treating the symbol as safe to change or delete; do not proceed on the strength of a zero.
- **MUST use `query({search_query: "concept"})` for concepts/flows, `context({name: "symbolName"})` for a named symbol, or `impact` for blast radius, on read-only callers, dependencies, imports, or execution flow.** Graph first; text search only for empty/`UNKNOWN`/literals.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method before MCP/CLI impact analysis.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis, and never read `UNKNOWN` as an all-clear — it means the walk could not answer, which is the one verdict that requires confirming by other means.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit before MCP/CLI graph change analysis.

## Resources

| Resource | Use for |
| --- | --- |
| `gitnexus://repo/the-website-factory/context` | Codebase overview, check index freshness |
| `gitnexus://repo/the-website-factory/clusters` | All functional areas |
| `gitnexus://repo/the-website-factory/processes` | All execution flows |
| `gitnexus://repo/the-website-factory/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
| --- | --- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
