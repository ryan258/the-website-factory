# Factory acceptance — 2026-09-21

## Ready for local client demonstrations

The master now includes 20 module families, 41 rendered variants, four fictional business compositions, an interactive Living Style Guide, and a visual workshop. The agency composition has six main pages, four case studies, and a contact receipt page. The workshop adds its catalog, living style guide, and four composition previews: 17 HTML pages in the complete review build.

The client-copy command selects a preset, excludes the workshop, style guide, and unused presets, removes unselected page trees, resets identity/contact configuration, and retains disabled delivery and noindex. Non-agency copies omit the agency project images and case studies. This is readiness for a local design review, not approval to publish a real business website.

## Measured verification

- Hugo Extended 0.166.0 and Dart Sass 1.104.1: isolated production-shaped build with no warnings; all generated pages pass metadata, H1, robots (noindex or indexable based on configuration), link, anchor, duplicate-ID, and bundle-budget checks.
- Seven focused factory tests pass (`scripts/test_factory.py`). They build all four client presets at both root and `/client/` URLs, test actual section reordering and omission, remove a previously generated page on rebuild, verify workshop exclusion, and verify output reconciliation preflight checks (refusing unowned targets, collision directories, symlinks, or edited files before modifying destination output).
- Four existing starter regression tests pass (`scripts/test_starter.py`), including a branded copy with edited colors and case metrics, refusal to overwrite an existing destination, and intentional broken-link detection.
- End-to-end local contact form verification passes (`scripts/check_contact.sh`), testing the Cloudflare Pages Function against local KV bindings with zero external deployment, verifying accepted, stored, redirected, rejected, and unconfigured paths.
- Twelve affected routes pass automated Chromium checks: Home, Services, About, Pricing, Work, Contact, the workshop, living style guide, and four preset previews. Each was checked in light/dark modes at 320, 600, 900, and 1200 pixels. Axe's WCAG A/AA checks report no violations; each page has one H1 and no horizontal document overflow.
- All 41 expanded workshop variants pass axe checks in both themes and overflow checks at 320, 390, 600, 900, and 1200 pixels. Native catalog and FAQ controls respond to Enter. The catalog, style guide, and disabled contact page work with JavaScript disabled. Preview contact links stay inside their fictional composition, and the receipt page does not imply an actual submission.
- Current compressed styles: shared main CSS approximately 5.5 KB; workshop-only CSS approximately 2.0 KB. The workshop stylesheet is not loaded by client pages. Contact remains the only page with executable application JavaScript.
- Screenshots for the workshop and all four business compositions are saved under `reports/` for visual review.

Evidence files: `reports/factory-browser-checks.json`, `reports/factory-workshop-checks.json`, and the desktop/mobile PNGs. Test results were measured locally; no external form submission was sent.

## Limits and client handover

Lighthouse scores from the original five-page demo are historical and are not current factory scores. No new broad Lighthouse run was performed. Automated accessibility checks do not establish full WCAG conformance. Physical phone/tablet checks, complete manual screen-reader/zoom acceptance, and hosted performance remain separate checks for the selected client composition.

All showcased businesses, names, testimonials, and offers are fictional examples. Real identity, copy, imagery rights, service coverage, and any claims require client review. Hosting, domain configuration, indexing, live form receipt, and publication remain owner-controlled and have not been performed.

The prior demo and starter acceptance records are preserved in [reference-demo-acceptance.md](reference-demo-acceptance.md) and [starter-acceptance.md](starter-acceptance.md). Practical component expansion and low-fidelity planning workspace acceptance are documented in [component-library.md](component-library.md) and [workflow-acceptance.md](workflow-acceptance.md). Strategic direction, milestone status, and planned evolution are tracked in [roadmap.md](../roadmap.md).
