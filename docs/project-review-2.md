# Project Review 2: The Website Factory

**Review date:** 2026-09-23
**Reviewed commit:** `8d9643c` (`main`; the session branch is identical)
**Earlier review:** [project-review.md](project-review.md) (commit `1459cf5`). Almost every item there is done.

## TL;DR

The project is in **strong working shape**. Every check I ran passed, including speed audits that scored 100 out of 100.

But a few real problems remain. The biggest: **the live contact form shows price ranges nobody confirmed**, and **the live site has no way to reach you if the form is off**. Client copies for non-agency businesses (restaurants, clinics) still show agency wording. And the tool has no "page not found" page.

This file has seven parts. Read them in any order.

1. The zero-to-hero tour
2. Health check (what I ran)
3. Review of today's changes
4. Fix list (corrections), sorted by urgency
5. Making it an exceptional tool for AI professionals
6. Suggested order of work
7. Decisions only Ryan can make

---

## Part 1: Zero-to-hero tour

### The one-sentence version

It is a **website-making machine**. One master copy holds every building block. You pick blocks, fill in words, and it builds a fast, plain, safe website for one business.

### The big idea

- **Modules** are page sections, such as a hero banner, a services list, or FAQs. There are 30 modules with 61 layouts (called "variants").
- **Presets** are starting plans for a kind of business. There are 8: agency, contractor, consultant, local-service, clinic, restaurant, nonprofit, and `258webco` (your real studio).
- **The master** keeps everything. **A client copy** keeps only what one client needs.
- **Honesty rules** are built in. Unknown facts say "To be confirmed". A public build fails while any remain.

### The two faces

| Face | Who sees it | What it is |
| --- | --- | --- |
| Public site | Visitors | The 258 Web Co. site: Home, Services, Contact, Privacy |
| Workshop | You only | Planner, module catalog, and style guide at `/site-kit/` |

### The main parts

1. **Hugo** (a tool that turns text files into web pages) builds the site.
2. **Dart Sass** (a tool that builds style sheets) makes the look.
3. **Python scripts** check the setup, build the site, and make client copies.
4. **The planner** (`assets/js/workflow.js`) is a browser tool for writing a brief and a page plan. It saves only in your browser.
5. **AI tools** draft a page plan from a written brief using the Claude API (`scripts/draft_plan.py`).
6. **The MCP server** (`scripts/mcp_server.py`) lets AI agents drive the factory. MCP means Model Context Protocol: a standard way to give an AI tools.
7. **The contact endpoint** (`functions/api/contact.js`) is a small Cloudflare program. It stores enquiries for 90 days.
8. **Checks** test links, accessibility, speed, honesty, and safety.

### How a client site gets made

1. Write a brief, in the planner or as a text file.
2. Optionally, let Claude draft a page plan (`draft_plan.py`, a paid call).
3. Compile the plan into a preset (`from_plan.py`).
4. Make a client copy (`new_site.py --guided`).
5. Replace every "To be confirmed" with a real fact.
6. Build, check, and write the handover report (`handover.py`).

### Where things live

| What | File |
| --- | --- |
| Which preset is live | `data/factory.json` |
| Module rules | `data/modules.json` |
| Pages, sections, and words | `data/presets/<preset>.json` |
| Name, menu, colors, fonts | `data/site.yaml` |
| Contact form budget choices | `data/contact.yaml` |
| Validation rules | `scripts/factory.py` |
| Output checks | `scripts/check_site.py` |
| Claims check | `scripts/claims.py` |
| Deploy | `.github/workflows/deploy.yml` (manual button only) |

### The safety rules that make it special

- A push to `main` **never** deploys. Deploying needs a manual button and a tick box.
- The form and the endpoint turn on **together or not at all**.
- Client copies start with **no** live settings, approvals, or search-engine indexing.
- The site loads **nothing** from other websites. A strict security rule (the CSP, or Content Security Policy) blocks it.

---

## Part 2: Health check (what I ran)

I downloaded the pinned Hugo and Dart Sass and ran every check.

| Check | Result |
| --- | --- |
| Site build (`build.py`) and output check (`check_site.py`) | ✅ Passed |
| All unit and contract tests (`npm test`: 86 Python tests and 25 contact endpoint cases) | ✅ Passed |
| Lint (`npm run lint`) | ✅ Passed |
| Claims check, strict | ✅ Passed (but see C1 and H2) |
| Browser and accessibility checks, 5 pages | ✅ Passed |
| Workshop checks, 61 layouts | ✅ Passed |
| Component and planner checks | ✅ Passed |
| Local Cloudflare contact test (`check_contact.sh`) | ✅ Passed |
| Lighthouse speed audit | ✅ **100 speed, 100 accessibility** on every page. About 49 KB and 4 requests per page. |
| New client copy (restaurant) build and tests | ✅ Passed (but see H5) |
| New client copy with a 50-letter name | ❌ **Build failed** (see H4) |

**Two setup problems I hit:**

- **Browser checks hung forever** when the browser did not match. The cause is a real bug (see H3), not just a setup problem.
- **Lighthouse would not start** as the root user. It needs a `--no-sandbox` option (see M8).

---

## Part 3: Review of today's changes

Since the last review (`1459cf5`), 18 commits landed on 2026-09-23. They closed nearly every item from the first review.

### What they did well

- **Deploy is safe.** One "Accept enquiries" box turns the form and the endpoint on together.
- **Privacy page added.** It is clear and honest.
- **Fictional case studies removed** from the live site.
- **Contact endpoint hardened.** Hashed IP addresses, an origin check, a no-JavaScript error page, and chat-safe alerts.
- **AI tooling added.** JSON Schemas, `--json` reports with error codes, a claims check, Claude drafting, an MCP server, an eval harness, and a handover report.
- **Three new presets, five palettes, five font pairings, and guided setup.**
- **Link checks** for section anchors, deep links, and `mailto:`/`tel:` links.
- **Tests grew** with every feature.

### What today's changes got wrong or left open

| Commit | Problem | See |
| --- | --- | --- |
| `8cb0059` | Changed the budget help text from "Illustrative ranges" to "Rough ranges… Not a quote." The sample prices now read as real 258 Web Co. prices. | C1 |
| `c8fe7c2` | Ships all 5 font files (about 160 KB unused) to the live site. Fonts cover Latin letters only. | M6, M7 |
| `b5975c0` | Guided setup keeps all 5 fonts when you pick "modern". The command-line option removes them. | M5 |
| `50abef5` | Error codes come from matching message text. Some messages get the generic code `ERROR`. | M1 |
| `58cd06c` | The saved AI draft in `evals/recorded/` looks hand-made. No live AI run has been scored yet. | M13 |
| `5bfe4f5` | The privacy page promises deletion on request. The enquiry tool cannot delete. | H8 |

---

## Part 4: Fix list (corrections)

Each item has the problem, why it matters, and a proposed fix.

### 🔴 Critical: fix before accepting enquiries or going live

#### C1. The live contact form shows unconfirmed prices

- **Problem:** The budget choices on `/contact/` are "Under $2,400", "$2,400–$6,800", "$6,800–$15,000", and "$15,000+". They began as sample numbers labeled "Illustrative". Commit `8cb0059` changed only the help text. Nobody confirmed the numbers.
- **Where:** `data/contact.yaml`.
- **Why it matters:** Visitors read these as your real prices. `CLAUDE.md` says never invent prices. The claims check does not read this file, so it passed.
- **Fix:** You choose (see Part 7). Either confirm the ranges, or use non-price choices such as "Small project / Medium project / Large project / Not sure yet". Then add `data/contact.yaml` to the claims check (see H2).

#### C2. No way to reach 258 Web Co. when the form is off

- **Problem:** `data/site.yaml` has `email: ""`. If you deploy without ticking "Accept enquiries", the live site has **no contact route at all**. The privacy page also says to ask for deletion "through the contact form".
- **Why it matters:** A studio site nobody can contact loses every lead. A privacy promise with no way to act on it is a legal risk.
- **Fix:** Publish a real address (your domain mail forwarding is already in the setup guide). Add a check: a public build fails if the form is off and no email or phone is shown. Update the privacy text to name the email.

### 🟠 High: fix soon

#### H1. No "page not found" (404) page

- **Problem:** The build makes no `404.html`. Cloudflare Pages then treats the site as a single-page app. **Every mistyped address returns the home page with a "success" status.**
- **Why it matters:** Search engines see endless copies of the home page. Visitors get no "page not found" message.
- **Fix:** Add `layouts/404.html` (plain, with links home and to contact). Make `check_site.py` fail if `404.html` is missing.

#### H2. The claims check has blind spots

- **Problem:** `scripts/claims.py` reads only the preset JSON. It misses:
  - `data/contact.yaml` (the prices in C1),
  - `data/site.yaml` (description, tagline, social card),
  - page titles and descriptions in `content/*.md`,
  - case studies in `content/work/*.md`,
  - time promises such as "Live in weeks, not months" and "two to three weeks",
  - people's names (for example fictional team members).
- **Also:** An approval matches if its text appears *anywhere* in a sentence. Approving a short phrase can approve much more than intended.
- **Fix:** Scan the **built HTML** instead. It is the one place that holds everything visitors see. Add a `DURATION` rule. Make approvals match whole sentences, or give each claim an ID.

#### H3. Browser checks hang forever if the browser fails to start

- **Problem:** `browser-checks.cjs`, `check_workshop.cjs`, and `visual_check.cjs` start a local web server, then launch the browser. If the launch fails, the error path never closes the server. Node never exits. I reproduced this.
- **Why it matters:** A setup problem looks like a frozen check. CI waits up to its 30-minute limit.
- **Fix:** Start the server inside the `try`, and close it in `finally`. Or call `process.exit(1)` in the error handler.

#### H4. Long business names break new client copies

- **Problem:** `new_site.py` accepts names up to 60 characters. But page titles are "Page — Business Name", and `check_site.py` fails titles of 60 or more. I made a copy named "Northside Family Dental and Orthodontic Care Group" (50 letters). **Its first build failed.**
- **Fix:** Add an optional `short_name` for titles. Guided setup asks for it when the name is long. Or warn at creation time with a clear message.

#### H5. Client copies keep agency wording

A new **restaurant** copy still shows:

- "Start a project" in the header button (from `data/site.yaml`).
- "Tell us about your project", "Company", "Project type", "Budget range", and "Send project enquiry" on the form (`layouts/partials/contact-form.html`).
- "FORM / FUNCTION · BUILT WITH INTENTION · 01—04" in the hero artwork (`layouts/partials/factory/module.html`).

Other hard-coded text:

- Work images always say "fictional project design" in their alt text. A real client's real project would be mislabeled.
- The comparison table caption always says "Illustrative engagement options".
- **Fix:** Move form labels, fields, and choices into data, one block per preset. Restaurants get "Book a table", clinics get "Request an appointment", nonprofits get "Volunteer or donate". Make the header button and hero caption come from the preset. Put alt text and captions in data.

#### H6. The live preset holds unused fictional people

- **Problem:** `data/presets/258webco.json` still has unused sections: `team` (fictional "Alex Morgan" and "Sam Rivera"), `testimonials` (sample quotes), `areas`, and `resources`.
- **Why it matters:** One small edit adds them to a live page. The claims check skips unused sections and does not look for names.
- **Fix:** Delete unused sections from `258webco`. Make `factory.py` warn about unused section content in any preset.

#### H7. Unconfirmed time promises on the live site

- **Problem:** The live site says "Live in weeks, not months", "two to three weeks", and "three to five weeks".
- **Why it matters:** These are business promises. The claims check does not catch them (see H2).
- **Fix:** You confirm them, or soften them. Then add them to `approved_claims`.

#### H8. The privacy page promises deletion, but the tool cannot delete

- **Problem:** `scripts/enquiries.py` can only `list` and `export`. Deleting someone's enquiry needs a raw `wrangler` command.
- **Fix:** Add `enquiries.py delete --email ADDRESS`. It shows matches, asks for confirmation, then deletes. Add a test with the stand-in wrangler.

### 🟡 Medium: quality and polish

| # | Problem | Fix |
| --- | --- | --- |
| M1 | Error codes come from matching message text. "compressed bundle exceeds", "reference escapes base path", "formAction must be…", and "Destination must be…" all get the generic `ERROR`. | Create each error with its code where it happens. Add a test that no known message maps to `ERROR`. |
| M2 | `assets/js/contact.js` ignores the server's reason. A bad email, "too many tries", or "not open" all show "check your connection". | Show `result.error` when the server sends one. Keep the generic text for timeouts and network errors. |
| M3 | The visitor waits for the chat alert (up to 10 seconds), even after the enquiry is safely stored. | Send the alert with `context.waitUntil()` once stored. Reply right away. |
| M4 | Page descriptions live in three places: `data/site.yaml`, the preset, and `content/*.md`. The meta description and `llms.txt` already disagree on the home page. The home title is just "Home — 258 Web Co." | Use one source (the preset). Generate the rest at build time. Give the home page a real title, such as "258 Web Co. — Fast websites for small businesses". |
| M5 | Guided setup with "modern" fonts keeps all 5 font files. | Always pass the chosen pairing to `create()`. |
| M6 | The live site uploads 4 unused font files (about 160 KB) plus licenses. | Copy only the fonts in use into the output. |
| M7 | Fonts cover Latin letters only. Names like "Café Zoë" or "Łódź" fall back to a system font. | Offer Latin-extended files. Warn when site text uses letters the font lacks. |
| M8 | Lighthouse does not run in CI. `audit.mjs` cannot start as root. | Add a Lighthouse job to CI. Read extra Chrome options from an environment variable. |
| M9 | CI actions are pinned by version tag, not by exact commit. No Dependabot. | Pin actions to commit hashes. Add Dependabot for Actions, npm, and pip. |
| M10 | No check after deploy. | Add a smoke test: fetch the live site, check headers and CSP, check `/api/contact` answers as expected, check the canonical domain. |
| M11 | The README says Python 3.9+. The pinned `anthropic` 1.x library needs Python 3.10+. | Say 3.10+ for the AI tools and their tests. |
| M12 | `<html lang="en">` and all form and button text are hard-coded in English. | Move interface text to `data/strings.yaml`. Read the language from `hugo.toml`. |
| M13 | The eval harness has 3 briefs and 1 saved draft (hand-made). One sample per brief. No live run scored yet. | See Part 5, C1. |
| M14 | MCP server gaps: no tool annotations (read-only or destructive hints), no resources or prompts, older protocol version list, `validate_preset` drops errors that do not start with the slug, and `compile_plan` with a `name` renames the slug but not the preset's name. | See Part 5, A1. Fix the two small bugs directly. |
| M15 | Code is very dense. `workflow.js` has 16 lines over 400 characters. `factory.py` and `check_site.py` pack many statements per line. | Format one file at a time, with tests green after each. Split `workflow.js` using Hugo's built-in `js.Build` (no new tool needed). |
| M16 | Settings are read with a separate regular expression in five places (for example `noindex` in `check_site.py` and `browser-checks.cjs`). | One shared settings reader for Python. One for Node. |
| M17 | A client copy gets the master README with a one-line banner, and no CI workflow. | Generate a short client README and a client CI workflow. |
| M18 | Docs total about 2,900 lines across 14 files (before this review). `101-ways` alone is 951 lines. | Add `docs/index.md` ("start here", five links). Move history (brief, build decisions, old reviews) to `docs/history/`. |
| M19 | The Cloudflare middleware likely runs on **every** request, including images and styles. That uses Function quota and adds a small delay. | Add `static/_routes.json` so Functions run only for `/api/*` and `/.factory-build.json`. Verify on a preview deploy first. |
| M20 | The restaurant preset's menu lives at `/services/`. | Use a `menu` page key. Page addresses already follow the key. |

### 🟢 Low: tidy-up

- Inter's license is named `OFL.txt`, which needs a special case in code. Rename it to `OFL-inter.txt`.
- `setup.py` calls `extractall` without `filter='data'`. Newer Python versions warn about this.
- Many `read_text()` calls have no `encoding='utf-8'`. They may break on Windows.
- `build.py --serve` does not send the `_headers` security rules. A local preview can hide a CSP problem. Reuse the server from `qa-paths.cjs`.
- No `/.well-known/security.txt`.
- `data/site.yaml` keeps agency leftovers the live site does not use (`work_notice`, `case_notice`, `plans`, `cta`, `process`, and Work and Pricing menu entries).
- Invalid submissions count toward the rate limit. This is acceptable; document it.

---

## Part 5: Making it an exceptional tool for AI professionals

The core is already rare: **strict data contracts, honest placeholders, and hard quality gates**. Agents need exactly those. The proposals below turn that core into a tool AI professionals would recommend.

Each proposal has a goal, a solution, and a rough size (S, M, or L).

### A. Agent-native interface

#### A1. Upgrade the MCP server (M)

- **Goal:** Any agent can use the factory safely without reading the code.
- **Solution:**
  - Add tool **annotations**: `readOnlyHint` for read tools and `destructiveHint` for `build_site` and `create_client_site`.
  - Add **resources**: modules, presets, schemas, and the house rules as readable documents.
  - Add **prompts**: "brief to site", "claims review", and "release check" as ready-made workflows.
  - Add a `screenshot` tool that returns page or module images, so agents can **see** their result.
  - Add a `diff_preset` tool that shows what a change would do before writing it.
  - Limit `create_client_site` to one allowed parent folder.

#### A2. Errors an agent can fix by itself (S)

- **Goal:** Agents repair mistakes in a loop instead of guessing.
- **Solution:** Every error gets a stable code, a JSON path (for example `/pages/home/sections/2/variant`), and a `hint` ("choose one of: cards, rows"). This builds on M1.

#### A3. A self-repairing draft loop (M, paid API calls)

- **Goal:** From brief to a checked draft in one command, with fewer human fixes.
- **Solution:** Draft → validate → send the error codes back to Claude → re-draft (at most 2 rounds) → claims check → build → screenshots → review file. A human approves before anything is published. Say the cost before each run.

#### A4. Claude Code skills and hooks for the house process (S)

- **Goal:** Every Claude Code session follows the same steps.
- **Solution:**
  - Skills in `.claude/skills/`: `new-client-site`, `claims-review`, `release-check`.
  - A hook that runs `factory.py` and `claims.py` before each commit.
  - A **session-start hook** that installs Hugo and Dart Sass in cloud sessions. This session had to download Hugo by hand.

### B. Trust and provenance (make honesty the headline feature)

#### B1. A fact ledger per client (M)

- **Goal:** Every fact on a site can be traced to its source.
- **Solution:** `data/facts.json` lists each fact, where it came from (brief line, email, call date), who confirmed it, and when. Sections point to fact IDs. A public build fails on any fact without a confirmed entry. This replaces loose text matching in `approved_claims`.

#### B2. Scan what visitors actually see (S)

- **Goal:** No blind spots.
- **Solution:** Run the claims check on the built HTML. Add rules for durations, phone numbers, addresses, and people's names. Flag unused fictional content. (This is H2 and H6, done as a feature.)

#### B3. A signed handover (S)

- **Goal:** The client confirms facts in writing.
- **Solution:** `handover.py` includes the fact ledger and the claims status, with a sign-off line per fact.

### C. Measure AI quality honestly

#### C1. A real eval suite (M, paid when run live)

- **Goal:** Know whether a prompt or model change helps or hurts.
- **Solution:**
  - 15–20 test briefs, at least two per preset.
  - **Adversarial briefs:** one that asks for fake five-star reviews, and one with hidden instructions inside the brief text ("ignore your rules").
  - Several runs per brief, with the spread of scores shown.
  - Cost and time per run.
  - Results saved over time, so trends are visible.
  - Compare models and effort levels side by side.

#### C2. Plain-language scoring (S)

- **Goal:** Drafts stay readable for everyone.
- **Solution:** Add a reading-level score (for example Flesch-Kincaid) to evals and to `check_site.py` as a warning.

#### C3. Speed and visual checks in CI (S)

- **Solution:** Run Lighthouse and the screenshot comparison in CI (M8), with saved reports.

### D. Fit any business, not just agencies

#### D1. Forms by business type (M)

- **Solution:** Form fields, labels, and choices come from data (H5). Ready-made forms: booking, appointment request (with a "do not send health details" notice), volunteer or donate, and quote request.

#### D2. Richer search data by business type (S)

- **Solution:** Generate structured data (schema.org) from the same facts: `Restaurant` with opening hours, `MedicalClinic`, `NGO`, and `LocalBusiness`.

#### D3. Other languages (M)

- **Solution:** Interface text in a strings file, and the page language from settings (M12).

### E. Delivery and repeat income

#### E1. A client repository kit (S)

- **Solution:** `new_site.py --repo` adds a client CI workflow, a preview-deploy workflow, `_routes.json`, and a short README. It never pushes on its own.

#### E2. Care-plan monitoring (M)

- **Goal:** Support the monthly care plans in the 101-ways guide.
- **Solution:** A script that checks each client site weekly: up, HTTPS valid, headers present, speed budget met, form endpoint answering. It writes a short report you can send.

#### E3. Full enquiry tools (S)

- **Solution:** `enquiries.py delete` (H8), plus a monthly summary.

### F. Developer experience

#### F1. A "doctor" command (S)

- **Goal:** Setup problems give a clear fix, not a frozen screen.
- **Solution:** `python3 scripts/doctor.py` checks Hugo, Sass, Python version, Node, and the browser. It prints one fix per problem. It would have caught both setup problems in Part 2.

#### F2. Readable code (M)

- **Solution:** Format and split the dense files (M15), one at a time, with tests green after each.

#### F3. A docs map (S)

- **Solution:** `docs/index.md` and a history folder (M18).

---

## Part 6: Suggested order of work

1. **Decide C1, C2, and H7** (prices, email, time promises). Only you can. See Part 7.
2. **Small safe fixes:** H1 (404 page), H3 (hang), H6 (remove fictional people), M2, M5, M11.
3. **Claims check sees everything:** H2 and B2 together.
4. **Client fit:** H4 and H5 (short names, data-driven forms and wording).
5. **Privacy tooling:** H8 (delete command).
6. **CI and operations:** M8, M9, M10, M19.
7. **Agent upgrades:** A2, then A1, then A4.
8. **Fact ledger and evals:** B1, then C1.
9. **Growth:** D1–D3, E1–E2.

Steps 1–5 are small and low-risk. Steps 7–9 are bigger. Each could hit problems I cannot predict yet, so each should start with a short spec.

---

## Part 7: Decisions only Ryan can make

1. **Budget ranges on the contact form (C1):** confirm the four price ranges, use size words instead, or remove the budget question.
2. **Public contact email (C2):** which address the site should show, if any.
3. **Time promises (H7):** are "two to three weeks" and "three to five weeks" true for you?
4. **Unused fictional content (H6):** OK to delete the unused sections from the `258webco` preset?
