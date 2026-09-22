# Factory acceptance — 2026-09-21

## Ready for local client demonstrations

The master includes modular families, rendered variants, five business compositions (`agency`, `contractor`, `consultant`, `local-service`, `258webco`), an interactive Living Style Guide, and a visual workshop. The agency and 258webco compositions include full multi-page flows with validated sections and disabled contact intake. The workshop adds its catalog, living style guide, and composition previews.

The client-copy command selects a preset, excludes the workshop, style guide, and unused presets, removes unselected page trees, resets identity/contact configuration, and retains disabled delivery and noindex. Non-agency copies omit the agency project images and case studies. This is readiness for a local design review, not approval to publish a real business website.

## Measured verification

- Hugo Extended 0.166.0 and Dart Sass 1.104.1: isolated production-shaped build with no warnings; all generated pages pass metadata, H1, robots (noindex or indexable based on configuration), link, anchor, duplicate-ID, and bundle-budget checks. Self-hosted Inter variable font is optimized/subsetted to 20.5 KB.
- Ten focused factory tests pass (`scripts/test_factory.py`). They build client presets at both root and `/client/` URLs, test actual section reordering and omission, remove a previously generated page on rebuild, verify workshop exclusion, verify output reconciliation preflight checks (refusing unowned targets, collision directories, parent file conflicts, symlinks, edited files, or untracked static assets `.html`, `.js`, `.css`, `.map` before modifying destination output), and verify crash-resilient manifest recording for interrupted publications.
- Five starter regression tests pass (`scripts/test_starter.py`), including a branded copy with edited colors and case metrics, refusal to overwrite an existing destination, intentional broken-link detection, and verification that client scaffolding inherits zero deployment resources, bucket names, KV IDs, or active intake variables from the master.
- Planner-to-preset compilation tests pass (`scripts/test_from_plan.py`), verifying conversion of planner JSON exports into schema-valid presets with normalized hierarchy, required hero/services sections, and item contract enforcement.
- End-to-end local contact form verification passes (`scripts/check_contact.sh`), testing the Cloudflare Pages Function against local KV bindings with zero external deployment, verifying accepted, stored, redirected, rejected, unconfigured, and unopened intake paths. Failure paths (storage errors, notification errors, unopened intake, 90-day retention TTL, and 5-request/10-minute IP rate limiting) are verified offline via 13 test cases in `scripts/test_contact_endpoint.mjs`.
- Security middleware (`functions/_middleware.js`) and headers (`static/_headers`) actively block external access to build inventories and dotfiles (`/.factory-build.json`).
- Affected routes pass automated Chromium checks: Home, Services, Pricing, Work, Contact, the four case studies, the form return page, the workshop, the living style guide, and preset previews. Each was checked in light/dark modes at 320, 600, 900, and 1200 pixels. Axe's WCAG A/AA checks report no violations; each page has one H1 and no horizontal document overflow.
- All expanded workshop variants pass axe checks in both themes and overflow checks at 320, 390, 600, 900, and 1200 pixels. Native catalog and FAQ controls respond to Enter. The catalog, style guide, and disabled contact page work with JavaScript disabled. Preview contact links stay inside their fictional composition, and the receipt page does not imply an actual submission.
- Current compressed styles: shared main CSS approximately 5.5 KB; workshop-only CSS approximately 2.0 KB. The workshop stylesheet is not loaded by client pages. Contact remains the only page with executable application JavaScript.
- Screenshots for the workshop and business compositions are saved under `reports/` for visual review.

Evidence files: `reports/factory-browser-checks.json`, `reports/factory-workshop-checks.json`, and the desktop/mobile PNGs. Test results were measured locally; no external form submission was sent.

## Limits and client handover

Lighthouse scores from the original five-page demo are historical and are not current factory scores. No new broad Lighthouse run was performed. Automated accessibility checks do not establish full WCAG conformance. Physical phone/tablet checks, complete manual screen-reader/zoom acceptance, and hosted performance remain separate checks for the selected client composition.

All showcased businesses, names, testimonials, and offers are fictional examples. Real identity, copy, imagery rights, service coverage, and any claims require client review. Hosting, domain configuration, indexing, live form receipt, and publication remain owner-controlled and have not been performed.

The prior demo and starter acceptance records are preserved in [reference-demo-acceptance.md](reference-demo-acceptance.md) and [starter-acceptance.md](starter-acceptance.md). Practical component expansion and low-fidelity planning workspace acceptance are documented in [component-library.md](component-library.md) and [workflow-acceptance.md](workflow-acceptance.md). Strategic direction, milestone status, and planned evolution are tracked in [roadmap.md](../roadmap.md).
