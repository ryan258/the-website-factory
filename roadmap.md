# The Website Factory Roadmap

**Strategic Direction:** Operate a web agency with an internal, reusable production system. The agency storefront is the default output; the workshop is a separate internal preview. Prioritize completing the brief-to-handover cycle with real projects and measuring where reuse helps before expanding the library. See [the agency workflow](docs/agency-workflow.md).

**Current interface step:** A functional low-fidelity project workspace supports saved briefs, page plans, editable section copy, reordering, human review, exported design handoffs, and direct plan-to-preset compilation into verified factory presets (`scripts/from_plan.py`). Direct AI integration and automated remote deployment pipelines remain future work. The existing component catalog is supporting reference at `/site-kit/catalog/`.

**Current Baseline (2026-09-22):**
- **Architecture & Build:** Pinned Hugo Extended 0.166.0 + Dart Sass 1.104.1 via Hugo Pipes (`@use`, css.Sass, `hugo:vars`). System-independent Python build helper (`scripts/build.py`) with preflight output reconciliation protecting untracked static assets (`.html`, `.js`, `.css`, `.map`), colliding, parent-conflicting, or edited files, plus crash-resilient manifest recording for interrupted publications. Optimized, self-hosted Inter variable font subsetted to 20.5 KB. Configurable search-engine visibility (`hugo.toml` `params.noindex`, `HUGO_PARAMS_NOINDEX` env var).
- **Hosting & Forms:** Cloudflare Pages default (`wrangler.toml`) with same-origin Pages Function (`functions/api/contact.js`) for durable enquiry storage in Cloudflare KV (`ENQUIRY`) with 90-day data retention TTL (`expirationTtl`), client IP rate limiting (5 submissions per 10 minutes), optional `NOTIFICATION_WEBHOOK` forwarding, explicit per-deployment intake gating (`ENQUIRY_ENABLED = "true"`), durable storage-first acknowledgment (502 on storage failure; best-effort email notification once stored), optional R2 image bucket declaration (`IMAGES_BUCKET`), and strict security middleware/headers blocking access to internal build inventories (`functions/_middleware.js`, `static/_headers`).
- **Component & Module Library:** 30 module families spanning 61 variants across heroes, services, features, case studies, logos/partners, team/business credentials, process steps, timeline/milestones, bento clusters, FAQs, pricing, comparison, practical decision support, hours, policies, and contact modules. Decoupled contact form service items across preset pages. Contracts enforced via `data/modules.json` and `scripts/factory.py`.
- **Visual Workshop & Living Style Guide:** Reference catalog at `/site-kit/catalog/` showcasing all 61 variants with native disclosure controls, plus an interactive Living Style Guide at `/site-kit/style-guide/` detailing design tokens, typography specimens, spacing scales, and atomic UI primitives. Low-fidelity workflow editor with 2 MB project backup limits and undo.
- **Business Presets:** 5 foundational business archetypes (`agency`, `contractor`, `consultant`, `local-service`, `258webco`) defined in `data/presets/*.json`, with `258webco` as the active studio preset.
- **Scaffolding & Plan Compiler (`scripts/new_site.py`, `scripts/from_plan.py`):** Deterministic creation of independent client copies supporting all 5 presets. Dedicated compiler (`scripts/from_plan.py`) converting low-fidelity planner JSON exports directly into validated factory presets adhering to module schema contracts, hierarchy rules, and item constraints.
- **Verification Harness & Quality Gates:** Deterministic test suites (`scripts/test_factory.py`, `scripts/test_starter.py`, `scripts/test_from_plan.py`, `scripts/test_contact_endpoint.mjs`, `scripts/check_site.py`, `scripts/check_contact.sh`) validating JSON schema, asset integrity, link resolution, output reconciliation (untracked `.js`/`.css`/`.map` detection, parent file conflict preflight, crash-resilient manifest writes), subpath deployments, robots visibility, deployment isolation, rate limiting, data retention TTL, and contact failure paths. Playwright/axe browser audit scripts (`scripts/check_workshop.cjs`, `scripts/check_components.cjs`, `scripts/check_workflow.cjs`, `scripts/browser-checks.cjs`) verifying 61 variants, planning workspace persistence/behavior, style guide accessibility, and zero overflow. Automated CI verification gates in `.github/workflows/deploy.yml`.

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
- Implemented durable delivery path: durable KV storage (`ENQUIRY`) and optional notification email (`EMAIL`) via Cloudflare Email Routing, with honeypot spam protection, length checks, and progressive-enhancement no-JS HTML redirect (`303 See Other`).
- Enforced explicit intake authorization (`ENQUIRY_ENABLED = "true"`) and storage-first receipt guarantee (returns 502 on storage failure without acknowledging receipt).
- Hardened client scaffolding in `scripts/new_site.py` to write unconfigured deployment files, preventing client copies from inheriting live bucket names, KV IDs, or active intake variables.
- Built local test harness (`scripts/check_contact.sh` and `scripts/test_contact_endpoint.mjs`) validating accepted, stored, redirected, rejected, unopened-intake, and failure paths.
- Hardened output reconciliation in `scripts/build.py` with parent directory conflict preflight and crash-resilient manifest recording.
- Enforced 2 MB backup capacity limits in `assets/js/workflow.js` and `scripts/check_workflow.cjs`.
- Made `noindex` a configurable release parameter in `hugo.toml` and `scripts/check_site.py` (`HUGO_PARAMS_NOINDEX`).
- Created step-by-step account onboarding and deployment runbook in `docs/cloudflare-setup.md`.

### Milestone 6: Plan-to-Preset Compilation, Cloudflare Hardening, & Quality Gates
- Built planner-to-preset compilation engine (`scripts/from_plan.py` & `scripts/test_from_plan.py`) converting low-fidelity planning workspace JSON exports into validated factory presets (`data/presets/<slug>.json`).
- Introduced `258webco` production business preset and configured as active studio preset (`data/factory.json`).
- Hardened Cloudflare Pages contact function with IP-based rate limiting (5 req / 10 min) and 90-day retention TTL (`expirationTtl`).
- Implemented `NOTIFICATION_WEBHOOK` support for real-time enquiry alerting.
- Secured internal build inventories and dotfiles via Cloudflare Pages middleware (`functions/_middleware.js`) and cache/index headers (`static/_headers`).
- Extended output reconciliation in `scripts/build.py` to prevent untracked `.js`, `.css`, and `.map` files from lingering in production builds.
- Optimized self-hosted variable Inter font to 20.5 KB.
- Integrated automated verification quality gates into `.github/workflows/deploy.yml` blocking deployment on any validation, build, or test failure.

---

## Active & Planned Priorities

### Phase 4: Extended Link & Resource Validation Contracts
- Expand `scripts/factory.py` to validate external URL schemas and telephone/email links without violating local offline testing boundaries.
- Support deep in-page anchor verification across dynamically composed multi-section layouts.

### Phase 5: Multi-Provider Form Integration Surface
- Abstract the form partial to support alternative static form providers (e.g., static webhook endpoints, Formspree) alongside the current Cloudflare Pages Function default.
- Retain honest disabled-by-default behavior until host-specific form delivery is explicitly configured.

### Phase 6: Expanded Archetypes & Design Presets
- Add additional business archetype presets (e.g., clinic/healthcare, restaurant/hospitality, non-profit).
- Introduce curated font and palette pairing presets in `data/presets/` to accelerate visual differentiation during client scaffolding.

### Phase 7: Interactive Client Onboarding & Handover Tools
- Add an interactive prompt mode to `scripts/new_site.py` for guided preset selection, brand palette definition, and navigation structuring.
- Implement an automated acceptance report generator that creates a customized, clean `docs/acceptance.md` for client handover.

---

## Explicit Boundaries & Non-Goals

- **No Runtime CMS or Database Requirements:** The factory remains strictly static Hugo; content and composition are managed via version-controlled Markdown, YAML, and JSON.
- **No Client-Side Framework Overhead:** Components must use standard HTML5 semantic elements and modern CSS. JavaScript is reserved for progressive enhancements (such as form submission feedback) and is never required for core navigation or reading.
- **No Fabricated Performance or Legal Claims:** Default presets, sample case studies, pricing tables, and testimonials are explicitly labeled as fictional. Client copies do not inherit historical test scores or delivery guarantees.
