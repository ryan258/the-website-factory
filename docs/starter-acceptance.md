> Historical milestone acceptance for the reusable client starter. Current factory acceptance is in [acceptance.md](acceptance.md); milestone status is tracked in [roadmap.md](../roadmap.md).

# Reusable starter acceptance — 2026-09-21

## Implemented

- `data/site.yaml` centralizes name/wordmark, description, contact details, navigation, shared calls to action, process heading, sample notices, font, primary light/dark colors, and social-card text.
- Home headline/proof/section copy, page intros, contact panel copy, and pricing comparison copy are front matter. Pricing FAQ and contact budget options are separate YAML datasets. All six case-study comparison metrics are front matter.
- The social card is generated from the configured brand and copy. The former static branded image is superseded. Decorative artwork/icons and the dark CTA panel remain explicit design assets, documented for replacement.
- `new_site.py` creates an exclusive source-only client copy, sets its name and placeholder email, retains noindex, resets the base URL and form toggle, and excludes local dependencies, generated output, Python caches, Git state, historical reports, and old acceptance claims.
- Portable Python setup/build/static-check helpers require no npm packages. The setup helper downloads the pinned standalone compiler and verifies the GitHub release SHA-256 digest. The build helper checks Hugo/Sass versions and fails on warnings.
- Optional Node QA dependencies are pinned in a root package.json and lockfile. Browser and Lighthouse helpers find their project from their script location, discover generated routes, accept targeted route filters, and return nonzero on failure. Browser failures replace stale reports.
- Local links, navigation, assets, and font URLs account for a base-path deployment. The subpath test found and fixed a real root-relative navigation mismatch.

## Verification performed

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

## Boundaries and remaining operator checks

No Git repository was initialized and no staging, commits, pushes, deployment, domain changes, messages, or live form submissions were performed. The reference demo stays fictional and non-indexed. Form delivery remains disabled by default; the implemented backend is still Netlify Forms only. Generic static hosting is supported with submission disabled; other form providers need implementation.

The complete all-route browser and Lighthouse runs are provided as operator commands in README.md. Manual keyboard, screen-reader, real-device, live-host header/compression, and live form delivery acceptance remain open. Changing a client's content, branding or assets invalidates inherited performance/accessibility assumptions; every copy gets a fresh acceptance document rather than the demo's scores.
