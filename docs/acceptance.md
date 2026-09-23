# Acceptance

One file for all acceptance evidence. **Current** is what is true today. **History** keeps
earlier records unchanged, for reference; their numbers are not current results.

## Current — 2026-09-23

Verified locally on the `main` branch with Hugo Extended 0.166.0 and Dart Sass 1.104.1.

| Check | Result |
| --- | --- |
| Build and generated-output checks (`scripts/build.py`, `scripts/check_site.py`) | Pass |
| Factory tests (`scripts/test_factory.py`, all 7 sample presets as client copies) | 13 pass |
| Client-copy and guided setup tests (`scripts/test_starter.py`) | 8 pass |
| Plan compiler tests (`scripts/test_from_plan.py`) | 11 pass |
| Enquiry reader tests (`scripts/test_enquiries.py`, stand-in wrangler) | 4 pass |
| Schema and `--json` report tests (`scripts/test_schemas.py`) | 8 pass |
| Claims check tests (`scripts/test_claims.py`); live preset `--strict` | 7 pass; 0 open claims |
| AI drafting and brief-to-copy (`scripts/test_ai.py`, stand-in API) | 4 pass |
| MCP server (`scripts/test_mcp.py`) | 7 pass |
| Eval grader (`scripts/test_evals.py`); saved bakery draft | 5 pass; score 1.00 |
| Handover report (`scripts/test_handover.py`) | 2 pass |
| Palettes, fonts, outside form service, llms.txt (`scripts/test_library.py`) | 11 pass |
| Anchors, deep links, mailto/tel (`scripts/test_links.py`) | 6 pass |
| Contrast (`scripts/contrast.py`): site theme and 5 palettes, light and dark | Pass (4.5:1 minimum) |
| Contact endpoint cases (`scripts/test_contact_endpoint.mjs`) | 25 pass |
| Local Pages integration (`sh scripts/check_contact.sh`) | Pass |
| Lint (`npm run lint`: ruff pyflakes rules, `node --check`) | Pass |
| Browser checks, public site: Home, Services, Contact, Privacy, receipt; light/dark; 320–1200 px; axe WCAG A/AA | Pass |
| Browser checks on clinic, restaurant, and non-profit client copies, and on editorial, friendly, and readable font pairings | Pass |
| Workshop (7 compositions), component, and planner browser checks | Pass |
| Visual regression PNG codec self-test; baseline record and compare on this machine | Pass |

The public `258webco` site has four pages (Home, Services, Contact, Privacy) plus the
contact receipt. It shows no fictional case studies. The contact form stays disabled
unless the deploy workflow's **Accept enquiries** input switches the form and the
endpoint on together.

### Not verified

- No Lighthouse run. No hosted HTTPS, compression, cache, or CSP check.
- No live Claude API call: AI drafting was tested against a local stand-in, and only the bakery brief has a saved draft (hand-written to the same rules).
- The preview and production deploy workflows have not been run against Cloudflare.
- No live form submission, live enquiry export, or real Cloudflare deployment.
- No manual keyboard, screen-reader, zoom, or real-device review. Automated axe checks do
  not establish full WCAG conformance.
- The privacy notice describes what the code does. It has not had a legal review.

---

## History

These records are kept as written at the time. Tools, test counts, and hosting have
changed since (for example, forms moved from Netlify to Cloudflare Pages).

### Factory acceptance — 2026-09-21

#### Ready for local client demonstrations

The master includes modular families, rendered variants, five business compositions (`agency`, `contractor`, `consultant`, `local-service`, `258webco`), an interactive Living Style Guide, and a visual workshop. The agency and 258webco compositions include full multi-page flows with validated sections and disabled contact intake. The workshop adds its catalog, living style guide, and composition previews.

The client-copy command selects a preset, excludes the workshop, style guide, and unused presets, removes unselected page trees, resets identity/contact configuration, and retains disabled delivery and noindex. Non-agency copies omit the agency project images and case studies. This is readiness for a local design review, not approval to publish a real business website.

#### Measured verification

- Hugo Extended 0.166.0 and Dart Sass 1.104.1: isolated production-shaped build with no warnings; all generated pages pass metadata, H1, robots (noindex or indexable based on configuration), link, anchor, duplicate-ID, and bundle-budget checks. Self-hosted Inter variable font is optimized/subsetted to 20.5 KB.
- Ten focused factory tests pass (`scripts/test_factory.py`). They build client presets at both root and `/client/` URLs, test actual section reordering and omission, remove a previously generated page on rebuild, verify workshop exclusion, verify output reconciliation preflight checks (refusing unowned targets, collision directories, parent file conflicts, symlinks, edited files, or untracked static assets `.html`, `.js`, `.css`, `.map` before modifying destination output), and verify crash-resilient manifest recording for interrupted publications.
- Five starter regression tests pass (`scripts/test_starter.py`), including a branded copy with edited colors and case metrics, refusal to overwrite an existing destination, intentional broken-link detection, and verification that client scaffolding inherits zero deployment resources, bucket names, KV IDs, or active intake variables from the master.
- Planner-to-preset compilation tests pass (`scripts/test_from_plan.py`), verifying conversion of planner JSON exports into schema-valid presets with normalized hierarchy, required hero/services sections, item contract enforcement, and collision safety (verifying existing preset files and SHA-256 hashes remain completely unchanged during preview mode).
- End-to-end local contact form verification passes (`scripts/check_contact.sh`), testing the Cloudflare Pages Function against local KV bindings with zero external deployment, verifying accepted, stored, redirected, rejected, unconfigured, and unopened intake paths. Failure, security, and notification paths (storage errors, notification errors, unopened intake, 90-day retention TTL, best-effort burst rate limiting, and webhook HTTP non-2xx status handling) are verified offline via 16 test cases in `scripts/test_contact_endpoint.mjs`. The Pages dev integration check (`sh scripts/check_contact.sh`) runs as an automated quality gate on every push and PR in CI before any deployment can proceed.
- Security middleware (`functions/_middleware.js`) and headers (`static/_headers`) actively block external access to build inventories and dotfiles (`/.factory-build.json`).
- Affected routes pass automated Chromium checks: Home, Services, Pricing, Work, Contact, the four case studies, the form return page, the workshop, the living style guide, and preset previews. Each was checked in light/dark modes at 320, 600, 900, and 1200 pixels. Axe's WCAG A/AA checks report no violations; each page has one H1 and no horizontal document overflow.
- All expanded workshop variants pass axe checks in both themes and overflow checks at 320, 390, 600, 900, and 1200 pixels. Native catalog and FAQ controls respond to Enter. The catalog, style guide, and disabled contact page work with JavaScript disabled. Preview contact links stay inside their fictional composition, and the receipt page does not imply an actual submission.
- Current compressed styles: shared main CSS approximately 5.5 KB; workshop-only CSS approximately 2.0 KB. The workshop stylesheet is not loaded by client pages. Contact remains the only page with executable application JavaScript.
- Screenshots for the workshop and business compositions are saved under `reports/` for visual review.

Evidence files: `reports/factory-browser-checks.json`, `reports/factory-workshop-checks.json`, and the desktop/mobile PNGs. Test results were measured locally; no external form submission was sent.

#### Limits and client handover

Lighthouse scores from the original five-page demo are historical and are not current factory scores. No new broad Lighthouse run was performed. Automated accessibility checks do not establish full WCAG conformance. Physical phone/tablet checks, complete manual screen-reader/zoom acceptance, and hosted performance remain separate checks for the selected client composition.

All showcased businesses, names, testimonials, and offers are fictional examples. Real identity, copy, imagery rights, service coverage, and any claims require client review. Hosting, domain configuration, indexing, live form receipt, and publication remain owner-controlled and have not been performed.

### Low-fidelity workflow — local verification

2026-09-22. This records the planning prototype, not production readiness or client acceptance.

Implemented at `/site-kit/`: projects, editable briefs, ordered page plans, section wireframes and copy, explicit draft/approval state, actionable content checks, human review, design handoff, session undo, browser saving, JSON backup/import, and Markdown brief export. The component reference is at `/site-kit/catalog/`.

Targeted verification uses `node scripts/check_workflow.cjs` with isolated browser storage and a temporary local server. Coverage includes saved copy and section order across reloads; resume at the saved stage; undo after reopening; literal HTML in copy; backup download/import; malformed-import refusal; missing-content gating; revoking review and readiness after edits; competing-tab protection; enforcing the 2 MB backup limit by refusing and rolling back oversized edits while guaranteeing round-trip importability; and visible storage failure with export available. Scoped axe checks cover the five stages, with a separate dark-mode editor check; overflow is checked at 320, 900, and 1440 pixels.

The actual existing port-1314 preview was refreshed and exercised with a clearly named fictional walkthrough project. Its brief, one-page plan, and sample copy are saved in that browser. Human review checkboxes were left unconfirmed. A visual check identified inherited dark-mode paragraph colors; the editor now explicitly maintains readable neutral text.

Public and workshop builds passed their generated-output checks. The public build omits workshop routes and editor assets. No full project suite, screen-reader assessment, real client acceptance, deployment, or live form test was performed.

Limits: saves belong to the current browser and origin; exports are needed for portable backups. Undo is session-local. AI assistance prepares a prompt and accepts a pasted proposal; no model is connected. Handoff exports a plan, not a generated client website. Visual design and implementation accessibility still require their own reviews.

### Reusable starter acceptance — 2026-09-21

#### Implemented

- `data/site.yaml` centralizes name/wordmark, description, contact details, navigation, shared calls to action, process heading, sample notices, font, primary light/dark colors, and social-card text.
- Home headline/proof/section copy, page intros, contact panel copy, and pricing comparison copy are front matter. Pricing FAQ and contact budget options are separate YAML datasets. All six case-study comparison metrics are front matter.
- The social card is generated from the configured brand and copy. The former static branded image is superseded. Decorative artwork/icons and the dark CTA panel remain explicit design assets, documented for replacement.
- `new_site.py` creates an exclusive source-only client copy, sets its name and placeholder email, retains noindex, resets the base URL and form toggle, and excludes local dependencies, generated output, Python caches, Git state, historical reports, and old acceptance claims.
- Portable Python setup/build/static-check helpers require no npm packages. The setup helper downloads the pinned standalone compiler and verifies the GitHub release SHA-256 digest. The build helper checks Hugo/Sass versions and fails on warnings.
- Optional Node QA dependencies are pinned in a root package.json and lockfile. Browser and Lighthouse helpers find their project from their script location, discover generated routes, accept targeted route filters, and return nonzero on failure. Browser failures replace stale reports.
- Local links, navigation, assets, and font URLs account for a base-path deployment. The subpath test found and fixed a real root-relative navigation mismatch.

#### Verification performed

| Check | Result |
| --- | --- |
| Final production build | Exit 0; no warnings |
| Static generated-output checks | Exit 0; metadata uniqueness/lengths, H1s, noindex, references, anchors, CSS/JS budgets |
| Focused starter tests | 4 passed; isolated client build with changed branding, palette and metrics; existing-path refusal; invalid/nested destination refusal; missing-output and broken-link failures |
| New client bootstrap | Fresh temporary copy downloaded and SHA-256-verified Sass 1.104.1; built from outside its project directory with zero warnings |
| Browser checks | Home, Pricing, Contact, Fieldwork detail, and receipt page passed in light/dark modes at widths 320/600/900/1200; zero axe A/AA violations |
| Browser negative fixture | A local page with two H1s and no noindex produced a failed report and exit 1 |
| JavaScript syntax | Browser and Lighthouse scripts passed Node syntax checks |

The isolated client copy used the name “Cedar & Stone,” changed the accent to mint, changed case LCP/weight values, and built under `/client/`. The generated HTML/CSS checks confirmed the edited values and correct font/link paths. Temporary client copies were removed after tests. This does not create a real client project or publish a site.

Machine-readable evidence is in ignored `reports/starter-browser-checks.json` and `reports/browser-negative-fixture.json`. Historical Lighthouse reports remain historical; they were not rerun or transferred to generated clients.

#### Boundaries and remaining operator checks

No Git repository was initialized and no staging, commits, pushes, deployment, domain changes, messages, or live form submissions were performed. The reference demo stays fictional and non-indexed. Form delivery remains disabled by default; the implemented backend is still Netlify Forms only. Generic static hosting is supported with submission disabled; other form providers need implementation.

The complete all-route browser and Lighthouse runs are provided as operator commands in README.md. Manual keyboard, screen-reader, real-device, live-host header/compression, and live form delivery acceptance remain open. Changing a client's content, branding or assets invalidates inherited performance/accessibility assumptions; every copy gets a fresh acceptance document rather than the demo's scores.

### Acceptance evidence — 2026-09-21

#### Built and verified locally

- Five main pages, four fictional case-study detail pages, and a contact receipt page. The Hugo build reports 12 total outputs, including sitemap and robots; 10 are HTML pages.
- Hugo Extended 0.166.0 + Dart Sass 1.104.1. `hugo --minify --gc` completes with zero warnings after setting the documented PATH and writable temporary cache environment.
- Custom Sass modules with `@use`, responsive Grid/Flexbox, shared color/spacing variables, CSS custom properties, device-following dark mode, one breakpoint mixin, and a single fingerprinted CSS file with SRI.
- Latin-subset, self-hosted Inter variable font (43,620 bytes). SIL Open Font License included.
- Original case illustrations transformed by Hugo into WebP srcsets and JPEG fallbacks; explicit image dimensions and lazy loading. HTML/CSS hero adds no image request.
- Unique title, description, canonical URL, one H1, and `noindex` on all 10 HTML pages. Internal links resolve. Home Organization and Services FAQ JSON-LD, social card, favicon, touch icon, robots, and sitemap are generated.
- All five main pages and all four detail pages: axe WCAG A/AA tags report zero violations in light and dark modes. Each tested at widths 320, 600, 900, and 1200 with no document horizontal overflow.
- A 200% text-size probe at 600 pixels passes on all five main pages after fixing work-card result wrapping. This is a browser automation check, not a complete manual zoom/device acceptance.
- Keyboard probes: first focusable item is the skip link; Enter moves focus to main; mobile menu opens; FAQ disclosure toggles with Enter. A complete manual keyboard audit remains open.
- Form-enabled test build: simulated HTTP 503 preserves entered text, focuses the error, and permits retry; simulated HTTP 200 announces success and clears inputs. Form name and honeypot are posted. JavaScript-disabled HTML POST reaches a local mock. No message was sent to Netlify or any third party. Default production/local build keeps submission disabled.

#### Home performance evidence

A focused Lighthouse mobile run against the local production build served by Python on port 14722 returned:

| Measurement | Result | Brief target |
| --- | --- | --- |
| Performance | 97 | 100 preferred, 95 minimum |
| Accessibility | 100 | 100 |
| Largest Contentful Paint | 1,429 ms | Under 1,500 ms |
| Cumulative Layout Shift | 0 | Under 0.05 |
| Transfer weight | 100,500 bytes (~100.5 KB) | Under 150 KB |
| Requests | 6 | At most 10 |
| CSS gzip | ~3.7 KB | Under 20 KB |
| JavaScript gzip | 615 bytes, Contact only | Under 5 KB |

The first run while other local browser work was in progress scored 88 (slow Speed Index). The isolated repeat scored 97. Scores are environment-sensitive; this is not a claim of stable hosted performance. Reports are `reports/home-lighthouse.html` and `.json`. Subsequent final edits only adjusted pricing copy/spacing and source formatting; all-page production performance still needs the documented audit.

Home has no executable JavaScript. Contact has one same-origin script. No external scripts, font requests, analytics, or trackers are present. The local server does not provide host Brotli behavior; verify it after deployment. Lighthouse does not establish field INP.

#### Still open before full brief sign-off

- Run the supplied five-page mobile Lighthouse command and inspect every score, LCP, CLS, and network budget. The full run is left to the operator per the instruction to provide long-running commands rather than execute broad suites.
- Manual VoiceOver/NVDA, complete keyboard navigation, real-device layout, tap-target, and zoom acceptance. Automated axe passes do not establish full WCAG 2.2 AA conformance.
- Owner selection/approval of deployment, account, recipient, and any collection of submitted information; enable Netlify form detection and `HUGO_PARAMS_FORMENABLED=true` only afterward.
- Test an authorized synthetic submission on the live host, verify storage and notification delivery, and inspect no-JavaScript host error handling.
- Verify hosted HTTPS, compression, caching, CSP, canonical hostname, and performance. Keep the fictional domain untouched and `noindex` enabled.
- Git initialization, staging, commit, push, and publication remain owner-controlled. The folder started empty and outside a Git repository. No Git mutation was performed.

The site implementation is ready for review. External acceptance is not complete.
