# The Website Factory Roadmap

**Strategic Direction:** Maintain `the-website-factory` as a high-performance, kitchen-sink Hugo master with broad capability, intentional defaults, and easy subtraction. The repository houses a comprehensive library of modular sections, an interactive visual workshop at `/site-kit/`, pre-configured business presets, and an automated client scaffolding command that selects required features and prunes unneeded assets.

**Current Baseline (2026-09-21):**
- **Architecture & Build:** Pinned Hugo Extended 0.166.0 + Dart Sass 1.104.1 via Hugo Pipes (`@use`, css.Sass, `hugo:vars`). System-independent Python build helper (`scripts/build.py`) with manifest-based output reconciliation and unselected page pruning.
- **Component & Module Library:** 20 module families spanning 41 variants across heroes, services, features, case studies, logos/partners, team/business credentials, process steps, timeline/milestones, bento clusters, FAQs, pricing, comparison, and contact modules. Contracts enforced via `data/modules.json`.
- **Visual Workshop & Living Style Guide:** Live interactive workshop at `/site-kit/` showcasing all 41 variants with native disclosure controls, plus an interactive Living Style Guide at `/site-kit/style-guide/` detailing design tokens, typography specimens, spacing scales, and atomic UI primitives.
- **Business Presets:** 4 foundational business archetypes (`agency`, `contractor`, `consultant`, `local-service`) defined in `data/presets/*.json`.
- **Scaffolding Engine (`scripts/new_site.py`):** Deterministic creation of independent client copies, stripping the workshop, unused presets, unselected page trees, and unreferenced project images while enforcing disabled delivery and `noindex`.
- **Verification Harness:** Deterministic test suites (`scripts/test_factory.py`, `scripts/test_starter.py`, `scripts/check_site.py`) validating JSON schema, asset integrity, link resolution, subpath deployments, and negative edge cases. Playwright/axe browser audit scripts (`scripts/check_workshop.cjs`, `scripts/browser-checks.cjs`) verifying 41 variants, style guide accessibility, and zero overflow.

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

---

## Active & Planned Priorities

### Phase 4: Extended Link & Resource Validation Contracts
- Expand `scripts/factory.py` to validate external URL schemas and telephone/email links without violating local offline testing boundaries.
- Support deep in-page anchor verification across dynamically composed multi-section layouts.

### Phase 5: Multi-Provider Form Integration Surface
- Abstract the form partial to support alternative static form providers (e.g., Cloudflare Pages Forms, static webhook endpoints, Formspree) alongside the current Netlify Forms default.
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
