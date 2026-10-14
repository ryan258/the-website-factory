# Changelog

All completed milestones, historical fixes, and major iterations for The Website Factory. For upcoming and active priorities, see [roadmap.md](roadmap.md).

## Milestones

### Milestone 13: Component Library Expansion & Three Layouts per Family (2026-10-14)
- **Eight New Section Families:** Added 8 new practical section families addressing distinct visitor needs: `announcements` (cards, rows, spotlight), `booking` (steps, cards, rows), `delivery` (cards, definitions, table), `access` (cards, definitions, disclosures), `eligibility` (cards, checklist, disclosures), `downloads` (cards, rows, table), `specifications` (definitions, table, cards), and `updates` (timeline, cards, rows).
- **Uniform Three Layouts per Family:** Expanded all 31 existing families to three variants each, bringing the library to 39 families and 117 variants across the system.
- **Catalog Layout Comparison:** Added native radio toggle at `/site-kit/catalog/` offering `Full width` and `Compare layouts` (side-by-side comparison on desktop viewports >= 1200px, responsive column stacking on smaller screens) operable without JavaScript and keyboard-accessible.
- **Project Brief Enhancements:** Multiple independent project brief instances supported with unique instance IDs and isolated step validation.
- **Structured Contracts & Schema Hardening:** Updated `schemas/preset.schema.json` and `schemas/plan.schema.json` with strict type validation and required structured item fields for delivery, specifications, downloads, and updates.
- **Automated Verification:** Verified via `scripts/check_components.cjs` (Playwright WCAG A/AA across light/dark themes, 320/900/1440 widths, layout comparisons, unique IDs, planner choices), `scripts/test_three_layouts.py` (compilation and content preservation for all 117 variants), and `scripts/test_component_expansion.py` (item field contract enforcement for the 8 new families).
- **Follow-up (2026-10-14):** `test_three_layouts.py` and `test_component_expansion.py` now run in `npm test`. Indexable builds refuse an inquiry site whose contact form is off.

### Milestone 12: Review Remediation & Creator Workflow Improvements (2026-10-03)
- **Review Corrections Implemented & Verified:** All sixteen findings (F01–F16) from the October 3 review addressed and verified clean through `scripts/verify_review.py` (run `20261003T231543844201Z`, 21/21 gates passed).
- **Unified Operator CLI (`wf`):** Created root command runner (`scripts/wf.py`, executable `./wf`) providing unified entry points for `new`, `status`, `open`, `check`, `approve`, `handover`, and `backup`.
- **Creator Starter Compositions:** Added 3 creator starters (`creator-portfolio`, `creator-writer`, `creator-audio`) with `site_type: "creator"` and flexible `contact_mode` options (`inquiry`, `email`, `link`, `off`), supporting credential-free HTTPS action/resource links without forcing business services or inquiry forms.
- **Shared Scaffold Core:** Consolidated source-copy logic into `scripts/scaffold_core.py` with contract-versioned origin receipts (`scaffold-origin.json`) and atomic directory scaffolding for factory and vertical sites (`scripts/vertical_site.py`).
- **Release Gating & Content Review:** Explicit owner content review recording (`./wf approve` writing `data/content-review.json` with field/asset digests), build freshness binding (`.factory-receipt.json`), release ID verification (`factory-release.json`), and strict claims/placeholder gating for indexable releases.
- **Concurrency & Output Protection:** Implemented canonical sibling destination locking (`scripts/output_lock.py`) preventing output corruption or race conditions.
- **MCP Server Hardening:** Added JSON-RPC envelope validation, malformed type early rejection, preserving granular factory diagnostics with JSON path pointers and repair hints.
- **Functions Security Headers:** Enforced explicit security headers (`X-Content-Type-Options`, `Content-Security-Policy`, etc.) across all Cloudflare Pages Function response paths (JSON, HTML redirects, method rejections).
- **Planner Workspace UX:** Focused single-section accordion editing, layout variant switching, direct item field editing, typing-burst undo/redo grouping, and browser file-picker project saving with a 15 KB workshop gzip budget.

### Milestone 11: Planner Fidelity, Starter Round-Trip & Single-Pass Scaffolding (2026-09-29)
- **Planner Starter Fidelity:** `assets/js/workflow.js` exports versioned section content blocks (`contentVersion: 1`), keeping every renderer field, stable page keys, anchors, tones, palettes, and font pairings. Dedicated input controls allow editing individual item fields, image alts, and secondary actions directly, preventing paragraph-level AI copy proposals from overwriting item structures. Starter profiles in `layouts/_default/kit.html` are serialized via `readFile` strings to prevent Hugo map serialization from sorting keys and altering authored navigation order.
- **Plan Compiler Hardening (`scripts/from_plan.py`):** Schema-validates nested structured items and content blocks, resolves bare `#anchor` targets to section owning pages, strictly rejects multi-project export files, and safely restores starter item structures on exact prose matches without overwriting edited text.
- **Single-Pass Client Creation (`scripts/new_site.py`, `scripts/factory_run.py`):** `new_site.create()` accepts an in-memory `profile` kwarg, applying the compiled preset profile once prior to asset and page pruning. This eliminates the base-preset sculpting indirection (`BASE = 'consultant'`) and guarantees client copies retain their planned resources directly.
- **Gate & Runner Reliability:** Minified `data-enabled=true` form flags supported in `scripts/check_site.py`. CI workflows (`deploy.yml`, `preview.yml`) pinned to `ubuntu-24.04`. GitNexus code intelligence index and rules integrated into `AGENTS.md` and `CLAUDE.md`.
- **Fidelity Testing Harness:** `scripts/check_planner_fidelity.cjs` (Playwright browser test covering all starters, exports, reload, import, editing, undo, responsive layout, and scoped axe WCAG checks) and `scripts/test_plan_fidelity.py` (semantic fidelity, starter field preservation, legacy edit protection, and client copy verification).

### Milestone 10: Review Hardening & Schema Alignment (2026-09-26)
- **Streamed request payload cap:** `functions/api/contact.js` enforces a 64 KB limit counting received stream bytes with web-standard `Blob` parsing into `FormData`.
- **Schema-driven plan compiler validation:** `scripts/from_plan.py` uses `schemas.plan_schema` and `schemas.validate` directly, providing standardized JSON path diagnostics (`$.path`) while keeping relaxed acceptance for planner backup imports.
- **Site output audit:** `scripts/check_site.py` checks stylesheets for cross-origin assets with single-pass canonical URL parsing.
- **Build and runner failure handling:** temp file cleanup isolated to process-owned files (`scripts/build.py`) and rollback of partial copies on failure (`scripts/factory_run.py`).
- **Button destination enforcement:** `action_url` ensures only valid internal paths, anchors, or `mailto:`/`tel:` destinations are accepted, with bare `#anchor` targets scoped to the section's owning page.

### Milestone 9: Links, Fonts, and Guided Setup (2026-09-23)
- Section `anchor` ids with validated deep links; validated `mailto:`/`tel:` links rendered as clickable item text; output checks for invalid and Hugo-sanitized (`#ZgotmplZ`) links.
- Optional heading font, `data/fonts.json` pairings (Source Serif 4, Fraunces, Nunito, Atkinson Hyperlegible Next, Inter; all OFL-1.1), `--fonts`, font validation, and a 90 KB preload budget.
- `scripts/new_site.py --guided`: one question at a time with lettered choices for preset, palette, and fonts.
- Link and resource validation (Phase 4): section anchors, validated `/page/#anchor` deep links, and validated clickable `mailto:` and `tel:` links, with output checks for bad or unsafe links.

### Milestone 8: AI-Ready Production Tooling (2026-09-23)
- JSON Schemas for presets and AI plans, generated from the module registry; `--json` results with stable error codes.
- Claims check (`scripts/claims.py`) with owner approvals; release builds fail on "To be confirmed" placeholders.
- Claude-drafted page plans from a brief (`scripts/draft_plan.py`), one command from brief to checked client copy (`scripts/factory_run.py`), and an eval harness with test briefs (`scripts/eval_plans.py`).
- MCP server exposing the factory to agents (`scripts/mcp_server.py`, `.mcp.json`).
- Handover report generator, local visual regression check, and manual Cloudflare preview deploys.
- Clinic, restaurant, and non-profit presets; five contrast-checked palettes; outside form services via `formAction`; `llms.txt`.
- Phase 5 (form providers): any `https://` form service through `params.formAction`, with the built CSP extended for that origin only.
- Phase 6 (archetypes and design presets): clinic, restaurant, and non-profit presets; five contrast-checked palettes.
- Phase 7 (handover): `scripts/handover.py` writes the acceptance report for a client copy.

### Milestone 7: Launch Readiness Corrections (2026-09-23)
- Production deploy switches the contact form and `ENQUIRY_ENABLED` on together through one **Accept enquiries** workflow input, and fails if they disagree.
- Added a privacy notice page to the `258webco` preset, linked from the footer and the enabled form.
- Removed the fictional Work page and case-study claims from the `258webco` preset.
- Removed the unusable Pages email path from `functions/api/contact.js`, the unused `IMAGES_BUCKET` binding, and the duplicate pull request workflow; aligned the Pages project name and added CI and browser-launch timeouts.
- See `docs/project-review.md` for the full review and remaining proposals.

### Milestone 6: Plan-to-Preset Compilation, Cloudflare Hardening, & Quality Gates
- Built planner-to-preset compilation engine (`scripts/from_plan.py` & `scripts/test_from_plan.py`) converting low-fidelity planning workspace JSON exports into validated factory presets (`data/presets/<slug>.json`), with in-memory validation protecting existing files on colliding slugs.
- Introduced `258webco` production business preset and configured as active studio preset (`data/factory.json`).
- Hardened Cloudflare Pages contact function with IP-based rate limiting (best-effort 5 req / 10 min), 90-day retention TTL (`expirationTtl`), and HTTP response checking (`res.ok`) on `NOTIFICATION_WEBHOOK` calls.
- Implemented `NOTIFICATION_WEBHOOK` support for real-time enquiry alerting and documented true KV storage-first architecture in `HAPPY-PATH.md`.
- Secured internal build inventories and dotfiles via Cloudflare Pages middleware (`functions/_middleware.js`) and cache/index headers (`static/_headers`).
- Extended output reconciliation in `scripts/build.py` to prevent untracked `.js`, `.css`, and `.map` files from lingering in production builds.
- Optimized self-hosted variable Inter font to 20.5 KB.
- Integrated automated verification quality gates and local Pages integration tests (`sh scripts/check_contact.sh`) into `.github/workflows/deploy.yml`, gating production releases on explicit owner confirmation (`workflow_dispatch`).

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

### Milestone 4: Living Style Guide & Kitchen-Sink Expansion
- Expanded component collection to 20 module families / 41 variants with additions of `features` (grid, split), `logos` (grid, inline), `timeline` (vertical, cards), and `bento` (mosaic, compact).
- Dedicated interactive Living Style Guide at `/site-kit/style-guide/` covering color swatches (light/dark semantics and archetype tone accents), fluid typography specimens, 8-step spacing visualizer, buttons, badges, card primitives, form controls, tables, and native disclosures.
- Automated Playwright/axe WCAG A/AA validation covering all 41 variants and the style guide page across 320px–1200px viewports with zero horizontal overflow.

### Milestone 3: The Website Factory (Kitchen-Sink Master & Workshop)
- Composition-driven rendering engine (`layouts/partials/factory/`) executing declared ordered sections.
- 16 module families with 33 rendered variants documented in `data/modules.json` and demonstrated in `data/examples.json`.
- Visual workshop at `/site-kit/` including variant catalog and live preset previews.
- 4 business archetype presets (`agency`, `contractor`, `consultant`, `local-service`).
- Selective page copying and asset tree pruning in `scripts/new_site.py` and `scripts/build.py`.
- Manifest-tracked build output reconciliation protecting untracked and owner-modified files.

### Milestone 2: Reusable Client Starter
- Centralized site brand, navigation, and theme configuration in `data/site.yaml`.
- Initial client scaffolding script (`scripts/new_site.py`) with exclusive directory creation and placeholder domain defaults (`example.invalid`).
- Base-path and subpath link/asset resolution.
- Focused regression tests validating isolated builds, brand replacement, and broken-link detection.

### Milestone 1: Reference Marketing Site Baseline
- Complete 5-page agency marketing site plus 4 case study detail pages and contact receipt page.
- Responsive Sass architecture, dark/light theme tokens, self-hosted Inter variable font.
- Responsive WebP/JPEG image processing, HTML/CSS hero illustration without extra image requests.
- Automated axe checks reported no detected WCAG A/AA violations in the tested mobile and desktop views. This is scoped evidence, not accessibility conformance certification.
