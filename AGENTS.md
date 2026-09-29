# For AI agents

A Hugo site factory: a brief becomes a validated page plan, then a fast static site. Facts are never invented; unknowns stay "To be confirmed", and a public build fails while any remain.

**Machine interfaces**

- MCP server: `python3 scripts/mcp_server.py` (registered in `.mcp.json`). Tools: `list_modules`, `list_presets`, `get_preset`, `get_schema`, `validate_preset`, `check_claims`, `compile_plan`, `build_site`, `check_site`, `create_client_site`, `draft_plan`.
- JSON Schemas: [`schemas/preset.schema.json`](schemas/preset.schema.json) and [`schemas/plan.schema.json`](schemas/plan.schema.json), also at their `$id` URLs.
- `--json` on `factory.py`, `build.py`, and `check_site.py`. Every error has a stable `code`; most also have a JSON pointer `path` to the field at fault and a `hint` saying what to change. Repair the field the pointer names, then validate again.

**Rules**

- Validate before editing by hand: `validate_preset`, `check_claims`, `compile_plan`.
- `draft_plan.py` and `eval_plans.py --live` make paid API calls. Say so first.
- Add to `approved_claims` only when the business has confirmed the claim.
- Do not commit, push, deploy, or turn the contact form on unless the owner asked. Details: [CLAUDE.md](CLAUDE.md).

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
