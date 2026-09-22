# Client starter handover

1. Create a fresh copy with `scripts/new_site.py --preset agency|contractor|consultant|local-service` (choose one preset value). It refuses existing paths and keeps delivery disabled and `noindex` on.
2. Edit `data/site.yaml`: name/wordmark, email, address, hours, location, navigation, shared CTA, font, colors, social-card text. These are design inputs, not verified business facts.
3. Edit ordered sections and visible copy in `data/presets/<preset>.json`. Replace page metadata and Markdown, contact service choices, and selected case studies. See `docs/factory-guide.md` for module contracts and removal behavior. All six case metrics live in each case's front matter. Remove unused case files and replace original artwork deliberately.
4. Replace the default logo/favicon/touch icon and optional decorative hero artwork when the client has approved assets. Update font licenses if changing the typeface.
5. Run the pinned build and fast static checks. Run the browser checks after the layout/content pass. The default audit discovers all generated HTML routes; limit checks with CHECK_PATHS/AUDIT_PATHS for a bounded change.
6. Review copy, phone/tablet layouts, keyboard interactions, 200% text enlargement, and a screen reader. Recheck contrast after palette changes. Record what was actually tested in this instance's acceptance document.
7. Choose hosting. This version prepares Cloudflare Pages with a same-origin Pages Function for the form; other hosts require implementation. Configure recipient and enable collection only with owner approval. Keep the form disabled on generic static hosts.
8. The owner authorizes Git actions, deployment, indexing, domain changes, and any test messages separately. Verify headers, canonical URLs, HTTPS, compression, live delivery, and mobile performance on the chosen host.

## Boundaries

This is a source-copy starter, not a CMS, a live commercial agency, or a promise of perfect Lighthouse scores. It has no deployment automation or remote credentials. Creating a copy does not replace all sample text with production copy. Historical test evidence is intentionally not inherited.

`data/site.yaml` controls the primary UI palette and typeface. Fixed colors inside decorative artwork, the social background, and the dark closing banner are intentional art direction; replace these assets/styles for a fully different design. Font paths are base-path aware; subpath builds are covered by a generated-output test. Form processing on a subpath is not accepted without a live test: Pages Functions are served from the deployment root, not the subpath.

## Maintenance

Hugo and Sass pins live in `.hugo-version` and `.sass-version`; the host's HUGO_VERSION/DART_SASS_VERSION must match. QA packages are pinned in `package.json`/`package-lock.json`. Update these deliberately and rerun the focused checks. Installers never run during a build, and build helpers never publish.

Official integration references: [Hugo Sass variables](https://gohugo.io/functions/css/sass/), [Hugo text image filter](https://gohugo.io/functions/images/text/), and [Cloudflare Pages Functions](https://developers.cloudflare.com/pages/functions/).
