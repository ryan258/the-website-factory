# The Website Factory

A kitchen-sink Hugo website master: build a broad collection of reusable sections, layouts, and business presets, then sculpt each client site into a focused, coherent website.

The master keeps the full collection. Each client gets a separate copy with its own branding, content, page composition, and selected capabilities. TheWebsiteFactory, a fictional agency, is the reference design and one example composition.

## Direction and current state

The guiding principle is **broad capability, intentional defaults, easy subtraction**. The full collection belongs in the master and its visual workshop. A finished client site includes the sections that serve its visitors and that the business can supply and maintain.

This adopts the master-and-sculpt approach used in the sibling `jones-construction` project. Shared patterns can inform this implementation; contractor-specific content, business claims, approvals, and integrations must remain specific to their client.

**Available now:** 20 module families with 41 variants, a visual workshop at `/site-kit/`, an interactive Living Style Guide at `/site-kit/style-guide/`, four business presets, validated page composition, and a client-copy command that selects the preset and excludes the workshop. The fictional agency reference has six main pages, four case studies, and a disabled contact form. The other presets start with Home, Services, About, and Contact.

**Client review:** open `/site-kit/` to compare the agency, contractor, consultant, and local-service compositions. Open a catalog row to inspect its live variants, or visit `/site-kit/style-guide/` for design tokens and UI component specimens. All examples are labeled as fictional. Delivery and publication require real business information and a separate owner decision.

See [the factory guide](docs/factory-guide.md) for composition editing, module contracts, and the client handover workflow. See [101 ways to use this](docs/101-ways-to-use-this-for-fun-and-profit.md) for practical client plays, vertical presets, and monetization ideas. See [current acceptance](docs/acceptance.md) for measured verification and its limits. See [the roadmap](roadmap.md) for strategic direction, milestone status, and planned evolution.

## The kitchen-sink master

### Reusable section library

The library includes these section families:

| Family | Intended options |
| --- | --- |
| Hero and introduction | Text-led, split image, project-led, and compact introductions |
| Services | Cards, detailed service sections, comparisons, and related services |
| Features and capabilities | 3-column feature cards with bullets and alternating split graphic rows |
| Work and proof | Project galleries, case studies, before/after comparisons, testimonials, and supported results |
| Social proof and logos | Partner/client grid marks and subtle inline accreditation bars |
| People and business | About, team, values, credentials, and service areas |
| Process and answers | Process steps, FAQs, preparation guidance, and useful resources |
| Timeline and milestones | Connected vertical milestone spines and phase cards |
| Bento showcase | Asymmetric mosaic clusters and compact proof cards |
| Offers and contact | Pricing or scope guidance, calls to action, contact details, and inquiry forms |

Every module has a stable identifier, a clear purpose, documented content inputs, supported variants, dependencies, and an example. Required content is validated before a build; optional copy is omitted when absent. Sample testimonials, credentials, prices, coverage, and results remain clearly fictional until replaced with supported business facts.

### Visual workshop and Living Style Guide

The `/site-kit/` catalog shows the available modules and their variants with realistic example content. The living style guide at `/site-kit/style-guide/` documents design tokens (colors, fluid typography specimens, 8-step spacing scale) and atomic UI primitives (buttons, badges, marks, cards, forms, tables, and native disclosures). Native disclosure controls work with a keyboard and without JavaScript.

The workshop is a development and review surface. Client copies exclude it from emitted pages, navigation, search, and sitemaps. Keep the reference homepage a deliberate composition that demonstrates the design.

### Page composition and business presets

Each page declares its ordered section selection and variants through validated JSON configuration. Business identity, editorial content, visual theme, and page composition have separate configuration surfaces.

Choose from agency, contractor, consultant, and local-service presets. Presets select an initial composition; they do not establish which services a business offers or supply approved copy. Typography, imagery, colors, tone, and layout remain editable.

### Complete selection and removal

Section selections determine rendered modules. Page selections determine emitted content, navigation, and sitemap entries. Links to omitted pages, missing dependencies, unknown variants, and unknown modules fail validation. RSS is disabled, and no search index is implemented. Organization metadata follows the site identity; the former independently generated FAQ schema has been removed to avoid publishing questions absent from the selected composition.

Components use a compact shared stylesheet and native HTML controls. Workshop styles are loaded only by workshop pages; images are processed when referenced, and client scaffolds without a Work page omit the agency project images. The form script is limited to Contact pages. Removing a previously published route also needs an explicit redirect or retirement decision for that client.

## Sculpting a client site

The workflow is:

1. Create a separate client copy while preserving the master's complete library.
2. Choose a starting business preset and a clear visitor goal.
3. Select and arrange pages and sections; remove anything without a useful role.
4. Apply the client's visual identity and replace examples with accurate content and authentic imagery.
5. Review the complete visitor journey, including contact behavior and missing-content states.
6. Verify the selected site's generated output and relevant browser behavior before handover.

Use `--preset` with the copy command below. Edit ordered section declarations and their content in `data/presets/<preset>.json`; edit identity and the base theme in `data/site.yaml`. The factory guide gives an example.

Client copies must start without inherited approvals, historical performance guarantees, or connected delivery. Keep business facts and delivery settings explicit. The master remains reusable; individual client work belongs in its own copy.

## Factory files

| Purpose | File |
| --- | --- |
| Selected preset and workshop inclusion | `data/factory.json` |
| Module names, variants, required content, dependencies | `data/modules.json` |
| Ordered pages, sections, and editorial copy | `data/presets/<preset>.json` |
| Full workshop sample content | `data/examples.json` (master only) |
| Composition and component rendering | `layouts/partials/factory/` |
| Configuration validation and preset selection | `scripts/factory.py` |
| Focused copy, omission, and failure-path checks | `scripts/test_factory.py` |
| Expanded workshop, keyboard, and no-JavaScript checks | `scripts/check_workshop.cjs` |
| Strategic direction, milestone status, and planned evolution | `roadmap.md` |

## Build and preview

Requires Python 3.9+ for helper scripts, **Hugo Extended 0.166.0**, and **Dart Sass 1.104.1**. Node is optional and used only for browser/Lighthouse checks.

1. Install the pinned Hugo Extended binary from [official releases](https://github.com/gohugoio/hugo/releases/tag/v0.166.0) and place `hugo` on PATH.
2. Install the pinned standalone Dart Sass from [official releases](https://github.com/sass/dart-sass/releases/tag/1.104.1), or run the installer below. Automatic setup supports macOS/Linux arm64/x64 and verifies the release's SHA-256 digest. Windows users should put the standalone `sass` command on PATH.
3. Run these commands from the project folder:

```sh
python3 scripts/setup.py       # Only if .tools/dart-sass is not already present
python3 scripts/build.py       # Validates, builds, and checks isolated output before replacing generated files
python3 scripts/check_site.py  # Fast generated-output checks
python3 scripts/build.py --serve --port 1313
# Open http://127.0.0.1:1313/site-kit/ for the client workshop.
```

The helper scripts also work when called by absolute path from another directory. They find the project relative to their own location. The build helper uses a private Dart Sass installation if present and a writable temporary Hugo cache. It does not download tools or install anything implicitly.

`--serve` serves verified generated output on loopback. Rebuild after edits; it is not a live-reload server. Prefer the helper for client builds because it applies page selection, validates links, and reconciles removed routes. Direct Hugo commands bypass that selection and output-checking workflow. If using the private compiler, first run `export PATH="$PWD/.tools/dart-sass:$PATH"`. In restricted environments, also set `HUGO_CACHEDIR` to a writable absolute temporary directory.

## Create a client copy

```sh
python3 scripts/new_site.py ../cedar-studio --name "Cedar Studio" --preset contractor
cd ../cedar-studio
python3 scripts/setup.py
python3 scripts/build.py
python3 scripts/check_site.py
```

The destination parent must exist; the destination itself must not. Existing files are never overwritten. Copies inside the source project and source symlinks are rejected. Source templates, assets, content, data, scripts, pinned QA dependencies, and current starter instructions are copied. `.tools`, `node_modules`, generated output, historical reports, old acceptance claims, and `.git` are not copied.

The new name appears in the header, footer, page titles, structured data, and generated social card. The default email becomes `hello@example.invalid`. The selected composition, service choices, and initial accent follow the preset. Remaining copy and sample details are fictional until you deliberately replace them. The CLI does not invent real business facts or claim a client-ready content rewrite. Each copy starts at `example.invalid`, with form delivery disabled and `noindex` retained.

## Content and brand configuration

| Edit | File |
| --- | --- |
| Business name, wordmark, contact details, navigation, footer, CTA, font, light/dark palette, social-card text | `data/site.yaml` |
| Visible headings, introductions, section content and order | `data/presets/<preset>.json` |
| Browser titles and meta descriptions | Each section's `content/*/_index.md` |
| Contact budget choices and currency hint | `data/contact.yaml` |
| Contact form service choices | `data/services.yaml` |
| Pricing and comparison sections | Selected preset JSON |
| FAQ sections | Selected preset JSON |
| Workshop examples of every module | `data/examples.json` (master only) |
| Process steps and variants | Selected preset JSON |
| Case-study copy, images, scores, LCP, page weights | `content/work/*.md` |

Use plain text in YAML values; templates escape content. Preserve YAML indentation. Theme values use six-digit hex colors. Font configuration accepts a local `static/fonts/*.woff2` file, a plain family name, and the existing variable-font weight range. Include the font's license. Changing colors or fonts requires fresh contrast/layout/budget checks; a valid color string alone is not an accessibility guarantee.

Hugo passes theme values to Dart Sass through `hugo:vars`, compiles `@use` modules, minifies and fingerprints the stylesheet, and adds SRI. Font preloads and CSS URLs follow the base URL's path. Spacing, layout widths, and breakpoints remain developer-owned Sass tokens. The small factory illustration and default icon are reusable artwork; replace `partials/hero-art.html`, `partials/mark.html`, `static/favicon.svg`, and the touch icon if a client has its own visual identity. The social-card background is `assets/images/social-base.png`; text is generated at build time.

Add a case study by copying an existing `content/work/*.md` file and updating its unique filename, metadata, `image`, `alt`, `metric_label`, and all six `metrics` fields. Put the image in `assets/images/`; Hugo produces WebP srcsets and JPEG fallbacks. Keep sample disclaimers until results are backed by real evidence.

## Local quality checks

The Python checks require no package installation. They fail with a nonzero exit code for build warnings, missing links/assets, duplicate metadata, missing `noindex`, incorrect H1 counts, or oversized compressed CSS/JS bundles.

```sh
python3 scripts/build.py
python3 scripts/check_site.py
python3 scripts/test_starter.py
python3 scripts/test_factory.py
```

The focused starter test creates an isolated temporary client copy, changes branding and metrics, builds it under a subpath, checks its output, and deliberately introduces a broken link to prove the checker fails. It also verifies refusal to overwrite an existing destination. Temporary output is removed after the test.

Optional browser tooling uses pinned dependencies and a lockfile:

```sh
npm ci
npx playwright install chromium
```

Serve **production output**, not the live-reload development server, for performance measurement:

```sh
python3 -m http.server 14722 --bind 127.0.0.1 --directory public
```

In another terminal, run the broader checks when ready:

```sh
PREVIEW_URL=http://127.0.0.1:14722/ npm run check:browser
npm run audit -- http://127.0.0.1:14722/
PREVIEW_URL=http://127.0.0.1:14722/ node scripts/check_workshop.cjs
```

The standard browser and Lighthouse commands discover every generated `index.html`, including renamed/new case studies and the contact receipt page, and return nonzero on failure. Browser checks cover axe WCAG A/AA, one H1, `noindex`, light/dark modes, and widths 320/600/900/1200. Lighthouse checks Performance >=95, Accessibility 100, LCP <1.5 s, CLS <0.05, and Home <150 KB / <=10 requests. `CHECK_PATHS` or `AUDIT_PATHS` can limit a run, e.g. `CHECK_PATHS='["/","/pricing/"]'`. Use `SITE_OUTPUT` for an alternate build directory and `CHROME_PATH` for an existing Chrome binary. Reports are written under this project's ignored `reports/` directory, independent of the caller's working directory.

Automated checks do not establish manual keyboard, screen-reader, field INP, live form delivery, or production-host acceptance. Old demo scores are historical evidence, not inherited client guarantees.

## Hosting and forms

The generated site can be served by any static host. `netlify.toml` is an optional, pinned Netlify build recipe; its preview URL sets canonical URLs. It neither deploys nor connects an account. `_headers` is a Netlify/Cloudflare-style header file; other hosts need equivalent settings. Compression, HTTPS, cache headers, and CSP must be verified at the actual host.

The current **form backend is Netlify Forms only**, not a generic multi-provider adapter. On other hosts keep delivery disabled until a real integration is implemented. Set `HUGO_PARAMS_FORMENABLED=true` only after the owner authorizes deployment, enables Netlify form detection, and chooses the account/recipient. The enabled form uses a same-origin HTML POST with a honeypot; optional small JavaScript provides status and retains input on failure. No-JavaScript error handling depends on the host.

No inbox or account is configured. No form test is sent by the local checks. Test both submission paths with synthetic data only after explicit authorization, and verify actual receipt rather than trusting the success page. Do not enable indexing, use the fictional domain, or replace sample claims with unsupported claims.

## Source control and handover

The scripts do not initialize Git, stage, commit, push, or publish. `.gitignore` excludes local tools, dependencies, reports, build output, and caches. The owner controls repository setup and publication.

Read `docs/starter-guide.md` for the client handover sequence and `docs/acceptance.md` for this instance's evidence. The original reference workspace also retains its historical brief and build decisions; new client copies receive current starter documentation only.
