# The Website Factory

A web agency storefront backed by an internal website production system. Clients buy a website shaped around their business; reusable components, presets, and checks help us deliver it consistently.

## Direction and current state

The public site explains services, examples, scope, and the client journey. The internal factory keeps the broad section library and workshop. Each client gets a separate copy with its own branding, content, page composition, and selected capabilities.

The operating cycle is **brief → scope → assemble → client review → verify and hand over → improve the master**. Read [the agency workflow](docs/agency-workflow.md) for responsibilities and the two preview commands. The agency remains a fictional demonstration until real business details and launch readiness are established.

This adopts the master-and-sculpt approach used in the sibling `jones-construction` project. Shared patterns can inform this implementation; contractor-specific content, business claims, approvals, and integrations must remain specific to their client.

**Available now:** 30 module families with 61 variants, a low-fidelity project workspace at `/site-kit/`, a component reference at `/site-kit/catalog/`, an interactive Living Style Guide at `/site-kit/style-guide/`, four business presets, validated page composition, and a client-copy command that selects the preset and excludes the workshop. The fictional agency reference has the brief's five pages (Home, Services, Work, Pricing, Contact), four case studies, and a disabled contact form. The other presets start with Home, Services, About, and Contact.

**Internal planning:** run `python3 scripts/build.py --workshop --serve --port 1314` and open `/site-kit/` to create or resume a client project. Work through its brief, page plan, wireframe copy, review, and design handoff. The reference catalog at `/site-kit/catalog/` compares the agency, contractor, consultant, and local-service compositions. Open a catalog row to inspect its live variants, or visit `/site-kit/style-guide/` for design tokens and UI component specimens. All examples are labeled as fictional. Delivery and publication require real business information and a separate owner decision.

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
| Decision support | Service fit and alternatives; included versus separately agreed scope |
| Preparation and arrival | Preparation checklists, opening hours, directions, and access information |
| Menus and sessions | Readable item lists, price or scope tables, event agendas, and session cards |
| Practical help | Business-approved policies, definitions, and support routes |

All 30 families are selectable in the low-fidelity planner. New practical components include copy and accessibility guidance, plus blank planning sections; reference examples never become approved client copy automatically. See [the component expansion guide](docs/component-library.md).

Every module has a stable identifier, a clear purpose, documented content inputs, supported variants, dependencies, and an example. Required content is validated before a build; optional copy is omitted when absent. Sample testimonials, credentials, prices, coverage, and results remain clearly fictional until replaced with supported business facts.

### Visual workshop and Living Style Guide

The `/site-kit/catalog/` catalog shows the available modules and their variants with realistic example content. The living style guide at `/site-kit/style-guide/` documents design tokens (colors, fluid typography specimens, 8-step spacing scale) and atomic UI primitives (buttons, badges, marks, cards, forms, tables, and native disclosures). Native disclosure controls work with a keyboard and without JavaScript.

The workshop is an internal development surface, omitted from the default agency build. Client review focuses on the selected client site. Client copies exclude it from emitted pages, navigation, search, and sitemaps. Keep the reference homepage a deliberate composition that demonstrates the design.

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
| Cloudflare contact endpoint test harness | `scripts/check_contact.sh` |
| Cloudflare setup and deployment runbook | `docs/cloudflare-setup.md` |
| Contact form Pages Function endpoint | `functions/api/contact.js` |
| Expanded workshop, keyboard, and no-JavaScript checks | `scripts/check_workshop.cjs` |
| Practical component contract checks | `scripts/check_components.cjs` |
| Planning workspace behavior and persistence checks | `scripts/check_workflow.cjs` |
| Agency delivery workflow guide | `docs/agency-workflow.md` |
| Practical component library guide | `docs/component-library.md` |
| Planning workspace acceptance evidence | `docs/workflow-acceptance.md` |
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
# Open http://127.0.0.1:1313/ for the agency site.
# Internal workshop: python3 scripts/build.py --workshop --serve --port 1314
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
| Contact form service choices | the preset's `services` section (shared with the Services page) |
| Pricing and comparison sections | Selected preset JSON |
| FAQ sections | Selected preset JSON |
| Workshop examples of every module | `data/examples.json` (master only) |
| Process steps and variants | Selected preset JSON |
| Case-study copy, images, scores, LCP, page weights | `content/work/*.md` |

Use plain text in YAML values; templates escape content. Preserve YAML indentation. Theme values use six-digit hex colors. Font configuration accepts a local `static/fonts/*.woff2` file, a plain family name, and the existing variable-font weight range. Include the font's license. Changing colors or fonts requires fresh contrast/layout/budget checks; a valid color string alone is not an accessibility guarantee.

Hugo passes theme values to Dart Sass through `hugo:vars`, compiles `@use` modules, minifies and fingerprints the stylesheet, and adds SRI. Font preloads and CSS URLs follow the base URL's path. Spacing, layout widths, and breakpoints remain developer-owned Sass tokens. The small factory illustration and default icon are reusable artwork; replace `partials/hero-art.html`, `partials/mark.html`, `static/favicon.svg`, and the touch icon if a client has its own visual identity. The social-card background is `assets/images/social-base.png`; text is generated at build time.

Add a case study by copying an existing `content/work/*.md` file and updating its unique filename, metadata, `image`, `alt`, `metric_label`, and all six `metrics` fields. Put the image in `assets/images/`; Hugo produces WebP srcsets and JPEG fallbacks. Keep sample disclaimers until results are backed by real evidence.

## Local quality checks

The Python checks require no package installation. They fail with a nonzero exit code for build warnings, missing links/assets, duplicate metadata, unexpected robots/noindex state, incorrect H1 counts, or oversized compressed CSS/JS bundles.

```sh
python3 scripts/build.py
python3 scripts/check_site.py
python3 scripts/test_starter.py
python3 scripts/test_factory.py
sh scripts/check_contact.sh
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
PREVIEW_URL=http://127.0.0.1:1314/ node scripts/check_workshop.cjs
node scripts/check_components.cjs
node scripts/check_workflow.cjs
```

The standard browser and Lighthouse commands discover every generated `index.html`, including renamed/new case studies and the contact receipt page, and return nonzero on failure. Browser checks cover axe WCAG A/AA, one H1, `noindex`, light/dark modes, and widths 320/600/900/1200. Lighthouse checks Performance >=95, Accessibility 100, LCP <1.5 s, CLS <0.05, and Home <150 KB / <=10 requests. `CHECK_PATHS` or `AUDIT_PATHS` can limit a run, e.g. `CHECK_PATHS='["/","/pricing/"]'`. Use `SITE_OUTPUT` for an alternate build directory and `CHROME_PATH` for an existing Chrome binary. Reports are written under this project's ignored `reports/` directory, independent of the caller's working directory.

Automated checks do not establish manual keyboard, screen-reader, field INP, live form delivery, or production-host acceptance. Old demo scores are historical evidence, not inherited client guarantees.

## Hosting and forms

The generated site can be served by any static host. `wrangler.toml` is an optional, pinned Cloudflare Pages recipe; the deployment URL sets canonical URLs. It neither deploys nor connects an account. `_headers` is a Cloudflare/Netlify-style header file enforcing strict security defaults including CSP, clickjacking prevention, and `Strict-Transport-Security: max-age=31536000; includeSubDomains`. `wrangler.toml` declares the `ENQUIRY` KV namespace and optional `IMAGES_BUCKET` R2 binding. Compression, HTTPS, cache headers, and CSP must be verified at the actual host.

The current **form backend is a Cloudflare Pages Function** (`functions/api/contact.js`), not a generic multi-provider adapter. On hosts without Pages Functions keep delivery disabled until a real integration is implemented. Set `HUGO_PARAMS_FORMENABLED=true` only after the owner authorizes deployment and binds `ENQUIRY` (KV). With no binding present the endpoint returns 503 and accepts nothing. The public contact form notice is scoped to storage-only until live email receipt is confirmed. Step-by-step account setup, including the domain, the enquiry store, and notification email, is in [docs/cloudflare-setup.md](docs/cloudflare-setup.md). Verify the endpoint before enabling it with `sh scripts/check_contact.sh`, which builds a form-enabled site, serves it with `wrangler pages dev` against a local KV binding, and exercises the accepted, stored, redirected, rejected, and unconfigured paths. It deploys nothing and needs no Cloudflare account. The enabled form uses a same-origin HTML POST with a honeypot; optional small JavaScript provides status and retains input on failure. No-JavaScript error handling depends on the host.

No inbox or account is configured. No form test is sent by the local checks. Test both submission paths with synthetic data only after explicit authorization, and verify actual receipt rather than trusting the success page. Do not enable indexing, use the fictional domain, or replace sample claims with unsupported claims.

## Source control and handover

The scripts do not initialize Git, stage, commit, push, or publish. `.gitignore` excludes local tools, dependencies, reports, build output, and caches. The owner controls repository setup and publication.

Read `docs/starter-guide.md` for the client handover sequence and `docs/acceptance.md` for this instance's evidence. The original reference workspace also retains its historical brief and build decisions; new client copies receive current starter documentation only.
