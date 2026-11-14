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
- Never run `git add`, `git commit`, or `git push` unless the owner explicitly says so. Do not deploy or turn the contact form on unless the owner asked. Details: [CLAUDE.md](CLAUDE.md).

## Source change checks

Trace affected imports, callers, routes, templates, and focused tests with native repository searches and source reads before editing. Keep unresolved references explicit and follow Ryan's current verification instructions. Staging, commits, pushes, deployment, and publication require his explicit delegation of that action.
