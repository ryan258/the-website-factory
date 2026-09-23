# Project Review: The Website Factory

**Review date:** 2026-09-23
**Reviewed commit:** `1459cf5` (branch `claude/jolly-planck-xmitzy`, same as `main`)

> **Superseded:** see [project-review-2.md](project-review-2.md) for the current review.
>
> **Status update (2026-09-23):** Every Part 4 fix is done on `main`, except the code reformat (a linter was added instead). Part 5 is done too, except live preview in the planner (blocked by the site's security rules), cloud saving (outside the static-site design), and splitting the planner code (deferred). See Milestones 7 and 8 in `roadmap.md`.

## TL;DR

The project is in **good working shape**. Every automated check passes. The code is careful about honesty and safety.

But there are a few real problems. The biggest one: **the live contact form would refuse every message** if you deploy today. The docs also disagree with each other in a few places. And the tool is not yet "AI-ready" — nothing lets an AI agent use it directly.

This file has three parts:

1. What the project is (the "zero to hero" tour).
2. What to fix (corrections), sorted by how urgent they are.
3. How to grow it into a standout tool for AI professionals.

---

## Part 1 — What this project is

### The one-sentence version

It is a **website-making system**. One "master" copy holds every building block. You pick blocks, fill in words, and it builds a fast, plain website for a client.

### The two faces

| Face | Who sees it | What it is |
| --- | --- | --- |
| Public site | Visitors | The 258 Web Co. studio website (Home, Services, Work, Contact) |
| Workshop | You only | Planning tool, block catalog, and style guide at `/site-kit/` |

### The main parts

1. **Hugo** (a tool that turns text files into web pages) builds the site.
2. **Sass** (a tool that makes style sheets) builds the look.
3. **Modules** — 30 kinds of page sections, with 61 layouts. Listed in `data/modules.json`.
4. **Presets** — 5 ready-made starting plans for a business type. Stored in `data/presets/`.
5. **Python scripts** — check the setup, build the site, copy it for a new client.
6. **Planner** — a browser tool (`assets/js/workflow.js`) for writing a brief and page plan. It saves only in your browser.
7. **Plan compiler** — `scripts/from_plan.py` turns a planner export into a preset.
8. **Contact form backend** — `functions/api/contact.js`, a small Cloudflare program that stores messages.
9. **Checks** — Python and browser tests for links, accessibility, speed, and safety.

### How work flows

1. Write a brief in the planner.
2. Export the plan. Compile it into a preset.
3. Make a client copy with `scripts/new_site.py`.
4. Replace sample words with real facts.
5. Build, check, and hand over.

---

## Part 2 — Health check (what I ran)

I installed the pinned tools and ran every check.

| Check | Result |
| --- | --- |
| Site build (`build.py`) | ✅ Passed |
| Output check (`check_site.py`) | ✅ Passed |
| Factory tests (12) | ✅ Passed |
| Client-copy tests (6) | ✅ Passed |
| Plan compiler tests (11) | ✅ Passed |
| Contact endpoint tests (20 cases) | ✅ Passed |
| Browser + accessibility checks (9 pages) | ✅ Passed |
| Workshop checks (61 layouts) | ✅ Passed |
| Component checks | ✅ Passed |
| Planner checks | ✅ Passed |
| Live Cloudflare test (`check_contact.sh`) | ⏭️ Not run (needs `wrangler` download) |
| Lighthouse speed audit | ⏭️ Not run |

**Two setup problems I hit:**

- `scripts/setup.py` downloads Sass through the GitHub API. That API was blocked here. Without a token it is also limited to 60 calls per hour.
- The browser checks **hung with no time limit** when the browser did not match. They passed once I pointed them at the installed browser.

---

## Part 3 — Review of the latest changes

The latest merge (`1459cf5`) covers commits `a9e0caa` to `3f7b1a5`. It changed 39 files.

### What it did well

- **Plan compiler is more honest.** It now writes "To be confirmed" instead of made-up facts like "$100" or "Every Monday".
- **Plan compiler is safer.** It checks the new preset in memory. It no longer writes a temp file that could delete a real preset.
- **It refuses to overwrite** a preset unless you add `--force`.
- **Unknown section types now fail loudly** instead of being skipped quietly.
- **Webhook check is correct now.** A webhook that answers with an error no longer counts as success. It also stops waiting after 10 seconds.
- **Name mismatch is caught.** The site name in `data/site.yaml` must match the preset name.
- **The `/.well-known/` folder stays reachable**, so domain checks still work.
- **Contact tests are more reliable.** The test server is fully stopped between runs. The rate limit is now tested.
- **Intake is off by default** in `wrangler.toml`. That is the safe choice.

### What the latest changes got wrong or left open

These are listed in full in Part 4. The short list:

1. Turning intake off in `wrangler.toml` **breaks the production deploy**. The deploy builds a form that is switched on, but the server refuses all messages.
2. `HAPPY-PATH.md` still says a push to `main` deploys. It no longer does.
3. The real studio site still shows **four fictional case studies**.

---

## Part 4 — Fix list (corrections)

Each item has: the problem, why it matters, and a proposed fix.

### 🔴 Critical — fix before going live

#### C1. The live contact form will refuse every message

- **Problem:** The deploy workflow builds the form **switched on** (`HUGO_PARAMS_FORMENABLED=true`). But `wrangler.toml` sets `ENQUIRY_ENABLED = "false"`. Cloudflare reads `wrangler.toml` as the only source of truth. So every message gets a 503 error.
- **Where:** `.github/workflows/deploy.yml` (Build Production Site step) and `wrangler.toml` line 31.
- **Why it matters:** Visitors see an error. You get no leads. Nothing warns you.
- **Fix:** Make both settings come from one place. Two options:
  - A. The deploy job fails if the form is on but `ENQUIRY_ENABLED` is not `"true"`.
  - B. Add a second workflow input, "Accept enquiries". It sets both values together.

#### C2. No privacy notice, but the form collects personal data

- **Problem:** The form stores names, emails, and client IP addresses for up to 90 days. There is no privacy page.
- **Why it matters:** Many US states and other countries expect a privacy notice when you collect personal data.
- **Fix:** Add a short privacy page (what is stored, for how long, who to ask for deletion). Link it from the form and footer. Add a "privacy" module or page to presets.

#### C3. The real studio site shows fictional case studies

- **Problem:** `/work/` shows four made-up projects on the real 258 Web Co. site. Each is labeled "fictional".
- **Why it matters:** A buyer sees a studio with no real work. It hurts trust more than having no Work page.
- **Fix:** Remove the Work page from the `258webco` preset until real projects exist. Or show "Concept work" with a clear, single label. The home page proof strip (0 trackers, 0 KB JavaScript) is real and can stay.

### 🟠 High — fix soon

#### H1. Docs disagree about how deploys work

- `HAPPY-PATH.md` lines 75 and 99 say a push to `main` deploys. It now needs a manual button (`workflow_dispatch`).
- `HAPPY-PATH.md` step 4 says to add the KV binding in the dashboard. `docs/cloudflare-setup.md` says the dashboard **cannot** change it.
- `HAPPY-PATH.md` never mentions switching `ENQUIRY_ENABLED` to `"true"`.
- **Fix:** Make `docs/cloudflare-setup.md` the single deploy guide. Turn `HAPPY-PATH.md` into a short checklist that links to it.

#### H2. Email code that can never run

- **Problem:** `functions/api/contact.js` has an email path (`env.EMAIL`). Cloudflare Pages cannot bind email (the `wrangler.toml` comments say so). The roadmap still lists email as a finished feature.
- **Fix:** Remove the email path, or move the form to a Cloudflare Worker where email works. Update Milestone 5 in `roadmap.md`.

#### H3. Unused storage bucket in `wrangler.toml`

- **Problem:** `IMAGES_BUCKET` (R2 storage) is declared. No code uses it.
- **Why it matters:** If that bucket was never created, the deploy may fail. It also adds confusion.
- **Fix:** Remove it until a feature needs it.

#### H4. Project name mismatch

- **Problem:** `wrangler.toml` says `name = "website-factory"`. The deploy uses `--project-name=258webco`.
- **Fix:** Set `name = "258webco"` so local and CI deploys agree.

#### H5. Checks run twice on every pull request

- **Problem:** `test.yml` and `deploy.yml` both run on pull requests. `test.yml` is a smaller copy.
- **Fix:** Delete `test.yml`. `deploy.yml` already runs everything, including browser checks.

#### H6. Browser checks can hang forever

- **Problem:** The browser scripts have no overall time limit. In CI a hang can last up to 6 hours.
- **Fix:** Add `timeout-minutes: 30` to CI jobs. Add a launch timeout in `scripts/qa-paths.cjs`.

### 🟡 Medium — quality and polish

| # | Problem | Fix |
| --- | --- | --- |
| M1 | Social card alt text shows "258 Web Co.." (two periods). The name already ends with a period. | In `layouts/partials/head.html` line 16, use a dash or strip the trailing period. |
| M2 | Raw visitor IP addresses are stored as KV keys (`ratelimit:<ip>`). | Store a salted hash of the IP instead. |
| M3 | Rate-limit keys and enquiries share one storage space. Listing enquiries also lists rate-limit keys. | Use a separate KV namespace, or a clear prefix and list by `enquiry:` only. |
| M4 | Without JavaScript, errors show raw JSON text. | Return a simple HTML error page when the visitor did not ask for JSON. |
| M5 | Any website can post to the form. | Check the `Origin` header matches the site. This cuts spam. |
| M6 | Webhook text puts visitor input straight into chat tools (Slack or Discord). Text like `@channel` can ping everyone. | Escape `@` mentions, or send fields only as structured data. |
| M7 | There is no way to read enquiries except the Cloudflare dashboard. | Add a small `wrangler`-based export script (`scripts/enquiries.py list/export`). |
| M8 | `factory.py` reads `data/site.yaml` with a regex, not a YAML reader. A name in single quotes breaks it. | Handle single quotes, or add a tiny safe YAML subset reader. |
| M9 | A crashed `from_plan.py --write` can leave a `*.tmp.json` file in `data/presets/`. It then fails validation as a bad preset. | Write the temp file outside `data/presets/`, or ignore `*.tmp.json`. |
| M10 | Only 4 color tones are allowed (`yellow`, `clay`, `sage`, `blue`). They are hard-coded in two places. | Move tones into one data file. Validate against it. |
| M11 | `check_site.py` passes an indexable build that still uses `example.invalid`. | Fail when `noindex=false` and the base URL is `example.invalid`. |
| M12 | Budget choices on the real site say "Illustrative ranges". | Use real ranges, or remove the word "illustrative". |
| M13 | The structured data (JSON-LD) only has name, URL, and description. | Add `ProfessionalService` type, area served, and contact point. |

### 🟢 Low — tidy-up

- **Code style:** The Python and JavaScript are packed into very long single lines. That is hard to read and review. Add a formatter (`ruff format` for Python, `prettier` for JavaScript) and a linter in CI.
- **Package name:** `package.json` says `website-client-starter`. Rename to `the-website-factory`.
- **Doc sprawl:** 12 docs, some over 400 lines. Three are "acceptance" files that overlap. Merge them into one `docs/acceptance.md` with dated sections.
- **Setup script:** `setup.py` uses the GitHub API. Download from the plain release URL instead. No token or rate limit needed.
- **Agent guide missing:** There is no `CLAUDE.md` or `AGENTS.md`. AI coding tools must guess the rules. (See Part 5, A1.)

---

## Part 5 — Growing it into a standout tool for AI professionals

The core is strong: strict data contracts, honest placeholders, and hard quality gates. Those are exactly what AI agents need. The missing piece is **a way for AI to plug in**.

Each proposal below lists the goal and a concrete solution.

### A. Make it agent-ready (highest value)

#### A1. Add an agent guide (`CLAUDE.md` / `AGENTS.md`)
- **Goal:** Any AI coding tool follows the house rules from the first minute.
- **Solution:** A short file with: build and test commands, the "never invent facts" rule, file map, and the definition of done.

#### A2. Publish JSON Schemas for presets and modules
- **Goal:** AI output is checked by a standard tool, not only by custom Python.
- **Solution:** Generate `schemas/preset.schema.json` and `schemas/modules.schema.json` from `data/modules.json`. Use them in `factory.py`, the planner, and editor autocomplete. LLMs can use them for structured output.

#### A3. Build an MCP server for the factory
- **Goal:** Claude and other agents can run the factory as tools.
- **Solution:** A small MCP server (MCP = Model Context Protocol, a standard way to give AI tools) with tools like:
  - `list_modules`, `list_presets`
  - `validate_preset` (returns the same errors as `factory.py`)
  - `compile_plan` (wraps `from_plan.py`)
  - `build_site`, `check_site` (returns a pass/fail report)
  - `new_client_site`

#### A4. AI-assisted brief → plan
- **Goal:** Turn a client interview or notes into a first page plan in minutes.
- **Solution:** A script `scripts/draft_plan.py` that calls the Claude API with the module list and schema. It outputs a planner-format JSON. Every fact it cannot confirm is marked "To be confirmed". A human still approves in the planner.

#### A5. Machine-readable check reports
- **Goal:** Agents can read failures and fix them in a loop.
- **Solution:** Add `--json` to `factory.py`, `check_site.py`, and `build.py`. Each error gets a code, file, and path (for example `PRESET_MISSING_FIELD`).

### B. Trust, honesty, and safety (the project's strongest theme — make it a feature)

#### B1. Claim tracking
- **Goal:** Nothing false ever ships.
- **Solution:** Give each fact-like field a status (`sample`, `to-confirm`, `approved`). The production build fails if any `sample` or `to-confirm` text is present.

#### B2. AI content guardrails
- **Goal:** AI-drafted copy cannot slip in unsupported claims.
- **Solution:** A lint step that flags numbers, percentages, prices, and superlatives ("best", "#1") without a source note.

#### B3. Evaluation harness for AI drafts
- **Goal:** Measure how good AI-generated plans are over time.
- **Solution:** A folder of sample briefs with expected outcomes. Score each run on: schema valid, no invented facts, correct page count, accessibility pass.

### C. Deeper automation

#### C1. One command, brief to preview
- **Solution:** `factory run brief.md --preview` — draft plan, compile preset, build, check, and open a local preview.

#### C2. Client preview links
- **Solution:** Deploy each client copy to a Cloudflare Pages preview branch. It stays `noindex` with intake off.

#### C3. Visual regression tests
- **Solution:** Save screenshots of each module layout. Compare on every change. Playwright already supports this.

#### C4. Automatic handover report
- **Solution:** Generate a client `acceptance.md` from the check results (roadmap Phase 7).

### D. Planner upgrades

- **D1. Cloud save option.** Browser storage is easy to lose. Offer export to a file or a repo folder.
- **D2. Live preview.** Show the real module layout next to each planned section.
- **D3. Split `workflow.js`.** It is one 101-line file of very dense code. Split into small modules with tests.

### E. Library growth (from the roadmap, re-ordered)

1. **Privacy and legal page module** (needed now — see C2).
2. **More presets:** clinic, restaurant, non-profit (roadmap Phase 6).
3. **Font and color pairing presets**, checked for contrast automatically.
4. **Form provider options** beyond Cloudflare (roadmap Phase 5).
5. **`llms.txt` output** so AI search tools can read client sites cleanly.

---

## Part 6 — Suggested order of work

1. **Fix C1** (form refuses messages). Small change, big impact.
2. **Add a privacy page** (C2) and **decide on the Work page** (C3).
3. **Clean up docs and config** (H1–H5).
4. **Add `CLAUDE.md`, a formatter, and CI timeouts** (Low items, H6).
5. **Add JSON Schemas and `--json` reports** (A2, A5).
6. **Build the MCP server** (A3).
7. **Add AI-assisted brief drafting with claim tracking** (A4, B1, B2).
8. **Add the evaluation harness** (B3).

Steps 1–4 are small and low-risk. Steps 5–8 are bigger. Each could fail in ways I cannot predict yet, so each should start with a short spec.
