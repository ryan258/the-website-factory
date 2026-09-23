# The Website Factory Roadmap

**Strategic Direction:** Operate a web agency with an internal, reusable production system. The agency storefront is the default output; the workshop is a separate internal preview. Prioritize completing the brief-to-handover cycle with real projects and measuring where reuse helps before expanding the library. See [the agency workflow](docs/agency-workflow.md).

**Current interface step:** A functional low-fidelity project workspace supports saved briefs, page plans, editable section copy, reordering, human review, exported design handoffs, and direct plan-to-preset compilation into verified factory presets (`scripts/from_plan.py`). Claude can draft plans from a brief (`scripts/draft_plan.py`), and agents can drive the factory through its MCP server (`scripts/mcp_server.py`). The existing component catalog is supporting reference at `/site-kit/catalog/`.

**Current Baseline (2026-09-22):**
- **Architecture & Build:** Pinned Hugo Extended 0.166.0 + Dart Sass 1.104.1 via Hugo Pipes (`@use`, css.Sass, `hugo:vars`). System-independent Python build helper (`scripts/build.py`) with preflight output reconciliation protecting untracked static assets (`.html`, `.js`, `.css`, `.map`), colliding, parent-conflicting, or edited files, plus crash-resilient manifest recording for interrupted publications. Optimized, self-hosted Inter variable font subsetted to 20.5 KB. Configurable search-engine visibility (`hugo.toml` `params.noindex`, `HUGO_PARAMS_NOINDEX` env var).
- **Hosting & Forms:** Cloudflare Pages default (`wrangler.toml` with `ENQUIRY_ENABLED = "false"` safe default) with same-origin Pages Function (`functions/api/contact.js`) for durable enquiry storage in Cloudflare KV (`ENQUIRY`) with 90-day data retention TTL (`expirationTtl`), client IP rate limiting (best-effort 5 submissions per 10 minutes), optional `NOTIFICATION_WEBHOOK` forwarding with HTTP response validation (`res.ok`), explicit per-deployment intake gating (`ENQUIRY_ENABLED = "true"`), durable storage-first acknowledgment (502 on storage failure; best-effort email notification once stored), and strict security middleware/headers blocking access to internal build inventories (`functions/_middleware.js`, `static/_headers`).
- **Component & Module Library:** 30 module families spanning 61 variants across heroes, services, features, case studies, logos/partners, team/business credentials, process steps, timeline/milestones, bento clusters, FAQs, pricing, comparison, practical decision support, hours, policies, and contact modules. Decoupled contact form service items across preset pages. Contracts enforced via `data/modules.json` and `scripts/factory.py`.
- **Visual Workshop & Living Style Guide:** Reference catalog at `/site-kit/catalog/` showcasing all 61 variants with native disclosure controls, plus an interactive Living Style Guide at `/site-kit/style-guide/` detailing design tokens, typography specimens, spacing scales, and atomic UI primitives. Low-fidelity workflow editor with 2 MB project backup limits and undo.
- **Business Presets:** 8 business archetypes (`agency`, `contractor`, `consultant`, `local-service`, `clinic`, `restaurant`, `nonprofit`, `258webco`) defined in `data/presets/*.json`, plus 5 contrast-checked palettes in `data/palettes.json`, with `258webco` as the active studio preset.
- **Scaffolding & Plan Compiler (`scripts/new_site.py`, `scripts/from_plan.py`):** Deterministic creation of independent client copies supporting all 5 presets. Dedicated compiler (`scripts/from_plan.py`) converting low-fidelity planner JSON exports directly into validated factory presets adhering to module schema contracts, hierarchy rules, and item constraints, with pure in-memory preview validation protecting existing preset files from collision deletion.
- **Verification Harness & Quality Gates:** Deterministic test suites (`scripts/test_factory.py`, `scripts/test_starter.py`, `scripts/test_from_plan.py`, `scripts/test_contact_endpoint.mjs`, `scripts/check_site.py`, `scripts/check_contact.sh`) validating JSON schema, asset integrity, link resolution, output reconciliation (untracked `.js`/`.css`/`.map` detection, parent file conflict preflight, crash-resilient manifest writes), subpath deployments, robots visibility, deployment isolation, rate limiting, data retention TTL, and contact failure paths. Playwright/axe browser audit scripts (`scripts/check_workshop.cjs`, `scripts/check_components.cjs`, `scripts/check_workflow.cjs`, `scripts/browser-checks.cjs`) verifying 61 variants, planning workspace persistence/behavior, style guide accessibility, and zero overflow. Automated CI verification gates and local Pages integration tests (`sh scripts/check_contact.sh`) in `.github/workflows/deploy.yml`, with production deployment strictly gated behind manual owner authorization.

---

## Completed Milestones

### Milestone 1: Reference Marketing Site Baseline
- Complete 5-page agency marketing site plus 4 case study detail pages and contact receipt page.
- Responsive Sass architecture, dark/light theme tokens, self-hosted Inter variable font.
- Responsive WebP/JPEG image processing, HTML/CSS hero illustration without extra image requests.
- WCAG A/AA compliance verified via automated axe checks across mobile and desktop viewports.

### Milestone 2: Reusable Client Starter
- Centralized site brand, navigation, and theme configuration in `data/site.yaml`.
- Initial client scaffolding script (`scripts/new_site.py`) with exclusive directory creation and placeholder domain defaults (`example.invalid`).
- Base-path and subpath link/asset resolution.
- Focused regression tests validating isolated builds, brand replacement, and broken-link detection.

### Milestone 3: The Website Factory (Kitchen-Sink Master & Workshop)
- Composition-driven rendering engine (`layouts/partials/factory/`) executing declared ordered sections.
- 16 module families with 33 rendered variants documented in `data/modules.json` and demonstrated in `data/examples.json`.
- Visual workshop at `/site-kit/` including variant catalog and live preset previews.
- 4 business archetype presets (`agency`, `contractor`, `consultant`, `local-service`).
- Selective page copying and asset tree pruning in `scripts/new_site.py` and `scripts/build.py`.
- Manifest-tracked build output reconciliation protecting untracked and owner-modified files.

### Milestone 4: Living Style Guide & Kitchen-Sink Expansion
- Expanded component collection to 20 module families / 41 variants with additions of `features` (grid, split), `logos` (grid, inline), `timeline` (vertical, cards), and `bento` (mosaic, compact).
- Dedicated interactive Living Style Guide at `/site-kit/style-guide/` covering color swatches (light/dark semantics and archetype tone accents), fluid typography specimens, 8-step spacing visualizer, buttons, badges, card primitives, form controls, tables, and native disclosures.
- Automated Playwright/axe WCAG A/AA validation covering all 41 variants and the style guide page across 320px–1200px viewports with zero horizontal overflow.

### Milestone 5: Cloudflare Pages Deployment & Contact Function Integration
- Migrated default hosting & form delivery from Netlify Forms to Cloudflare Pages Functions (`functions/api/contact.js`).
- Implemented durable delivery path: durable KV storage (`ENQUIRY`), with honeypot spam protection, length checks, and progressive-enhancement no-JS HTML redirect (`303 See Other`).
- Enforced explicit intake authorization (`ENQUIRY_ENABLED = "true"`) and storage-first receipt guarantee (returns 502 on storage failure without acknowledging receipt).
- Hardened client scaffolding in `scripts/new_site.py` to write unconfigured deployment files, preventing client copies from inheriting live bucket names, KV IDs, or active intake variables.
- Built local test harness (`scripts/check_contact.sh` and `scripts/test_contact_endpoint.mjs`) validating accepted, stored, redirected, rejected, unopened-intake, and failure paths.
- Hardened output reconciliation in `scripts/build.py` with parent directory conflict preflight and crash-resilient manifest recording.
- Enforced 2 MB backup capacity limits in `assets/js/workflow.js` and `scripts/check_workflow.cjs`.
- Made `noindex` a configurable release parameter in `hugo.toml` and `scripts/check_site.py` (`HUGO_PARAMS_NOINDEX`).
- Created step-by-step account onboarding and deployment runbook in `docs/cloudflare-setup.md`.

### Milestone 6: Plan-to-Preset Compilation, Cloudflare Hardening, & Quality Gates
- Built planner-to-preset compilation engine (`scripts/from_plan.py` & `scripts/test_from_plan.py`) converting low-fidelity planning workspace JSON exports into validated factory presets (`data/presets/<slug>.json`), with in-memory validation protecting existing files on colliding slugs.
- Introduced `258webco` production business preset and configured as active studio preset (`data/factory.json`).
- Hardened Cloudflare Pages contact function with IP-based rate limiting (best-effort 5 req / 10 min), 90-day retention TTL (`expirationTtl`), and HTTP response checking (`res.ok`) on `NOTIFICATION_WEBHOOK` calls.
- Implemented `NOTIFICATION_WEBHOOK` support for real-time enquiry alerting and documented true KV storage-first architecture in `HAPPY-PATH.md`.
- Secured internal build inventories and dotfiles via Cloudflare Pages middleware (`functions/_middleware.js`) and cache/index headers (`static/_headers`).
- Extended output reconciliation in `scripts/build.py` to prevent untracked `.js`, `.css`, and `.map` files from lingering in production builds.
- Optimized self-hosted variable Inter font to 20.5 KB.
- Integrated automated verification quality gates and local Pages integration tests (`sh scripts/check_contact.sh`) into `.github/workflows/deploy.yml`, gating production releases on explicit owner confirmation (`workflow_dispatch`).

### Milestone 8: AI-Ready Production Tooling (2026-09-23)
- JSON Schemas for presets and AI plans, generated from the module registry; `--json` results with stable error codes.
- Claims check (`scripts/claims.py`) with owner approvals; release builds fail on "To be confirmed" placeholders.
- Claude-drafted page plans from a brief (`scripts/draft_plan.py`), one command from brief to checked client copy (`scripts/factory_run.py`), and an eval harness with test briefs (`scripts/eval_plans.py`).
- MCP server exposing the factory to agents (`scripts/mcp_server.py`, `.mcp.json`).
- Handover report generator, local visual regression check, and manual Cloudflare preview deploys.
- Clinic, restaurant, and non-profit presets; five contrast-checked palettes; outside form services via `formAction`; `llms.txt`.

### Milestone 7: Launch Readiness Corrections (2026-09-23)
- Production deploy switches the contact form and `ENQUIRY_ENABLED` on together through one **Accept enquiries** workflow input, and fails if they disagree.
- Added a privacy notice page to the `258webco` preset, linked from the footer and the enabled form.
- Removed the fictional Work page and case-study claims from the `258webco` preset.
- Removed the unusable Pages email path from `functions/api/contact.js`, the unused `IMAGES_BUCKET` binding, and the duplicate pull request workflow; aligned the Pages project name and added CI and browser-launch timeouts.
- See `docs/project-review.md` for the full review and remaining proposals.

---

## Active & Planned Priorities

### Open
- **Link and resource validation (Phase 4):** validate telephone and email links offline, and in-page anchors across composed sections.
- **Font pairings:** only the self-hosted Inter font ships today. Add licensed, self-hosted pairings alongside `data/palettes.json`.
- **Interactive onboarding:** a guided prompt mode for `scripts/new_site.py` (preset, palette, navigation).
- **First live AI runs:** record real drafts for the plumber and food-bank test briefs (`scripts/eval_plans.py --live --record`) and review the scores.
- **Planner code structure:** `assets/js/workflow.js` is compact and dense. Split it into modules only with a bundler step and the existing `check_workflow.cjs` coverage kept green.

### Done in Milestone 8
- Phase 5 (form providers): any `https://` form service through `params.formAction`, with the built CSP extended for that origin only.
- Phase 6 (archetypes and design presets): clinic, restaurant, and non-profit presets; five contrast-checked palettes.
- Phase 7 (handover): `scripts/handover.py` writes the acceptance report for a client copy.

### Decided against for now
- **Live preview inside the planner:** it would need a page embedded in a page, which the site's `frame-ancestors 'none'` security rule forbids. The planner links to each module's catalog entry instead.
- **Cloud saving for the planner:** the planner stays a browser tool with JSON export and import; saving elsewhere would need an account and a server, which the static-site boundary excludes.

---

## Explicit Boundaries & Non-Goals

- **No Runtime CMS or Database Requirements:** The factory remains strictly static Hugo; content and composition are managed via version-controlled Markdown, YAML, and JSON.
- **No Client-Side Framework Overhead:** Components must use standard HTML5 semantic elements and modern CSS. JavaScript is reserved for progressive enhancements (such as form submission feedback) and is never required for core navigation or reading.
- **No Fabricated Performance or Legal Claims:** Default presets, sample case studies, pricing tables, and testimonials are explicitly labeled as fictional. Client copies do not inherit historical test scores or delivery guarantees.
