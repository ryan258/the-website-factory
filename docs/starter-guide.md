# Client starter handover

1. Create a fresh copy with `scripts/new_site.py --guided`, or pass options: `--preset` (any file in `data/presets/`: `agency`, `contractor`, `construction`, `consultant`, `local-service`, `clinic`, `restaurant`, `nonprofit`, `258webco`), plus optional `--palette` and `--fonts`. Construction defaults to the earthworks palette and editorial fonts. It refuses existing paths and keeps delivery disabled and `noindex` on.
2. Edit `data/site.yaml`: name/wordmark, email, address, hours, location, navigation, shared CTA, font, colors, social-card text. These are design inputs, not verified business facts.
3. Edit ordered sections and visible copy in `data/presets/<preset>.json`. Replace page metadata and Markdown, contact service choices, and selected case studies. See `docs/factory-guide.md` for module contracts and removal behavior. All six case metrics live in each case's front matter. Remove unused case files and replace original artwork deliberately.
4. Replace the default logo/favicon/touch icon and optional decorative hero artwork when the client has approved assets. Each font in `static/fonts/` needs its `OFL-<name>.txt` license beside it; validation fails without one.
5. Run the pinned build and fast static checks. Run the browser checks after the layout/content pass. The default audit discovers all generated HTML routes; limit checks with CHECK_PATHS/AUDIT_PATHS for a bounded change.
6. Run `python3 scripts/claims.py` and confirm each listed claim with the owner. Review copy, phone/tablet layouts, keyboard interactions, 200% text enlargement, and a screen reader. Recheck contrast after palette changes (`python3 scripts/contrast.py`). Write this instance's acceptance document with `python3 scripts/handover.py --build --output docs/acceptance.md`, then add what was tested by hand.
7. Choose hosting. This version prepares Cloudflare Pages with an unconfigured `wrangler.toml` and client-specific setup guide (`docs/cloudflare-setup.md`). Intake requires creating a client-owned KV namespace and setting `ENQUIRY_ENABLED = "true"`. On other hosts, set `params.formAction` to an outside form service's `https://` address (see README, Hosting and forms). Configure recipient and enable collection only with owner approval. Keep the form disabled on generic static hosts.
8. The owner authorizes Git actions, deployment, indexing, domain changes, and any test messages separately. Verify headers, canonical URLs, HTTPS, compression, live delivery, and mobile performance on the chosen host.

## Boundaries

This is a source-copy starter, not a CMS, a live commercial agency, or a promise of perfect Lighthouse scores. It holds no remote credentials. The master's GitHub deploy workflow is manual and owner-only; a client copy needs its own. Creating a copy does not replace all sample text with production copy. Historical test evidence is intentionally not inherited.

`data/site.yaml` controls the primary UI palette and typeface. Fixed colors inside decorative artwork, the social background, and the dark closing banner are intentional art direction; replace these assets/styles for a fully different design. Font paths are base-path aware; subpath builds are covered by a generated-output test. Form processing on a subpath is not accepted without a live test: Pages Functions are served from the deployment root, not the subpath.

## Maintenance

Hugo and Sass pins live in `.hugo-version` and `.sass-version`; the host's HUGO_VERSION/DART_SASS_VERSION must match. QA packages are pinned in `package.json`/`package-lock.json`. Update these deliberately and rerun the focused checks. Installers never run during a build, and build helpers never publish.

Official integration references: [Hugo Sass variables](https://gohugo.io/functions/css/sass/), [Hugo text image filter](https://gohugo.io/functions/images/text/), and [Cloudflare Pages Functions](https://developers.cloudflare.com/pages/functions/).
