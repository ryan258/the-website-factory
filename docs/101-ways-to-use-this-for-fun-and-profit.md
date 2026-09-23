# 101 Ways to Use The Website Factory (For Fun & Profit)

A practical handbook for web sculptors, freelance operators, indie builders, and agency owners.

The Website Factory is built on a simple philosophy: **broad kitchen-sink capability, intentional defaults, and easy subtraction**. 20 module families, 41 render variants, four business presets, a living style guide, and a static core whose only application JavaScript is on the contact page.

Every entry below is written as a recipe: which preset to start from, which sections to stack, and which files to edit. Read "Read this first" once and all 101 become mechanical.

---

## Read this first

### What you need installed

| Requirement | Version | Notes |
| --- | --- | --- |
| Python | 3.9+ | Helper scripts only; standard library, no packages |
| Hugo **Extended** | 0.166.0 | Pinned. Non-extended Hugo cannot compile the Sass |
| Dart Sass | 1.104.1 | `python3 scripts/setup.py` installs it privately on macOS/Linux |
| Node | optional | Only for Playwright/axe/Lighthouse checks (`npm ci`) |

### The loop you will run hundreds of times

```sh
python3 scripts/factory.py      # validate configuration (fast, no build)
python3 scripts/build.py        # validate → build in a temp dir → check → publish to public/
python3 scripts/check_site.py   # re-check generated output
python3 scripts/build.py --serve --port 1313
# http://127.0.0.1:1313/            the selected composition
# http://127.0.0.1:1313/site-kit/   every module + the sample business compositions
# http://127.0.0.1:1313/site-kit/style-guide/   tokens, type scale, buttons, states
```

`--serve` is a plain static server over verified output. It is **not** live-reload: rebuild after every edit.

### How a page is actually assembled

```
data/factory.json          → { "preset": "agency", "workshop": true }
  └─ data/presets/<preset>.json
       ├─ name / label / tone            identity + accent seed
       ├─ pages.<key>.title/description  browser metadata for the workshop
       ├─ pages.<key>.sections[]         [{ module, variant, content }, …]  ← the page order
       └─ sections.<key>                 the actual words each section renders
data/modules.json          → what each module allows (variants, required fields, dependencies)
data/site.yaml             → business identity, navigation, font, light/dark palette
content/<page>/_index.md   → that page's <title> and meta description
```

`sections[].content` is a **key into the same file's `sections` object**. Changing the page order means reordering that array. Removing a section means deleting one array entry — the content block can stay, unused.

Fastest way to get a valid new section block: copy it out of the master's catalog data.

```sh
python3 -c "import json;print(json.dumps(json.load(open('data/examples.json'))['bento'],indent=2))"
```

`data/examples.json` holds one correct, fully-populated example of **all 20 modules**. Paste it under `sections`, rename the key, rewrite the words.

### The module catalog

| Module | Variants | Required top-level | Item fields |
| --- | --- | --- | --- |
| `hero` | `split`, `centered`, `compact` | title, intro, action | — (plus `secondary`, `note`, `art`) |
| `services` | `cards`, `rows` | title, items | title, text |
| `work` | `gallery`, `editorial` | title, items | title, text, image, url |
| `process` | `steps`, `rows` | title, items | title, text |
| `about` | `split`, `editorial` | title, intro, body | — (plus `aside`) |
| `team` | `cards`, `rows` | title, items | title, text, initials |
| `faq` | `accordion`, `open` | title, items | title, text |
| `pricing` | `cards`, `rows` | title, items, notice | title, text, value, bullets[] |
| `areas` | `cards`, `rows` | title, items, notice | title, text |
| `testimonials` | `quotes`, `featured` | title, items, notice | title, text |
| `stats` | `strip`, `cards` | title, items, notice | title, text |
| `cta` | `band`, `quiet` | title, intro, action | — |
| `contact` | `panel`, `compact` | title, intro, items, notice | title, text |
| `resources` | `cards`, `rows` | title, items | title, text, url |
| `comparison` | `table`, `cards` | title, items, notice | title, text, **scope**, **best** |
| `before-after` | `panels`, `stacked` | title, items, notice | title, text |
| `features` | `grid`, `split` | title, items | title, text, bullets[] |
| `logos` | `grid`, `inline` | title, items, notice | title, text |
| `timeline` | `vertical`, `cards` | title, items | title, text, phase |
| `bento` | `mosaic`, `compact` | title, items | title, text, badge, span (`large`) |

Every item needs a non-empty `title` **and** `text`, always. `label` is the small eyebrow line above a section heading. Hero `art` accepts `factory` (the illustration) or a keyword for the abstract treatment — `orbit` and `tiles` have dedicated styling.

### The four presets, as shipped

| Preset | Tone / accent | Pages | Home stack |
| --- | --- | --- | --- |
| `agency` | `yellow` `#ffc400` | home, services, about, contact, **work**, **pricing** | `hero/split` → `services/cards` → `work/gallery` → `process/steps` → `cta/band` |
| `contractor` | `clay` `#edb08e` | home, services, about, contact | `hero/split` → `services/cards` → `about/editorial` → `process/steps` → `areas/cards` → `cta/band` |
| `consultant` | `sage` `#b9d7bb` | home, services, about, contact | `hero/centered` → `services/cards` → `about/editorial` → `process/steps` → `resources/cards` → `cta/band` |
| `local-service` | `blue` `#a6cef7` | home, services, about, contact | `hero/split` → `services/cards` → `about/editorial` → `process/steps` → `areas/cards` → `cta/band` |

All four share `services`, `about`, and `contact` pages with the same stacks. Only `agency` ships the `work` gallery, case studies, `pricing`, `comparison`, and `before-after` — anything below that asks for those on another preset means adding the page yourself (recipe in the Appendix).

`tone` only seeds the accent when scaffolding and styles workshop previews. In a client copy, the real brand color is `theme.accent` in `data/site.yaml`.

### Ten rules validation will enforce (`scripts/factory.py`)

1. Every page's **first** section must be a `hero`, and it must be the page's **only** hero.
2. `home` and `contact` pages are mandatory in every preset.
3. The `work` module requires a page keyed `work`.
4. `pricing`, `areas`, `testimonials`, `stats`, `contact`, `comparison`, `before-after`, `logos` each require a `notice` string.
5. `comparison` items additionally require `scope` and `best`.
6. Module links must be **local page paths** (`/services/`) that exist in `pages` *and* have a content file. Schemes, hosts, query strings, and fragments are rejected outright.
7. Item `image` values must resolve to a real file under `assets/` (e.g. `images/foo.png`), no absolute paths, no `..`. Only the **`work`** module renders item images; elsewhere an `image` field validates but never appears.
8. Preset and page keys must match `[a-z][a-z0-9-]*`.
9. Pages need both `title` and `description`.
10. A content directory not listed in `pages` is dropped from the build (`site-kit/` survives only while `workshop` is `true`).

One more that bites on a real client site: the `work` module generates its own `alt` text as `"<item title> — fictional project design"` (`layouts/partials/factory/module.html:37`). Edit that template before publishing a site with real photography.

**Rule 6 is the one that surprises people.** You cannot put an outbound link in module content. Outbound links go in Markdown page bodies — `content/<section>/<slug>.md` renders its body through `single.html`. That is how directories, link lists, and case libraries work here.

### Checks that will fail your build (`scripts/check_site.py`)

- Page `<title>` (rendered as `Page — Site Name`) must be **under 60 characters**; meta description **under 155**.
- Titles, canonicals, and descriptions must be unique across every page.
- Exactly one `<h1>` per page; no duplicate element IDs.
- Every internal reference must resolve, anchors included.
- Each emitted CSS bundle under **20,000 bytes gzipped**; each JS bundle under **5,000 bytes gzipped**. Current shared CSS is ~5.5 KB compressed, workshop-only CSS ~2.0 KB.
- `<meta name="robots" content="noindex">` must be present on every page.

### Going live: the five things that are deliberately off

A fresh copy is built to be un-publishable by accident. To ship a real site you change all of these on purpose:

1. **`noindex`** defaults to true in `hugo.toml` (`params.noindex = true`) and is conditionally rendered in `layouts/partials/head.html`. `scripts/check_site.py` validates the expected robots tag. Build with `HUGO_PARAMS_NOINDEX=false` (or set `noindex = false` in `hugo.toml`) for a live, indexable release.
2. **`baseURL`** in `hugo.toml` is `https://example.invalid/`. Set the real domain.
3. **Form delivery** is off (`params.formEnabled = false`). The only implemented backend is a **Cloudflare Pages Function** (`functions/api/contact.js`): set `HUGO_PARAMS_FORMENABLED=true` after binding `ENQUIRY` (KV) and/or `EMAIL` (send_email) in a real account. On a host without Pages Functions, keep it off until you implement a backend.
4. **Sample copy** — every name, testimonial, statistic, price, and service area ships fictional and labelled. A new business name does not approve the rest of the text.
5. **Contact details** in `data/site.yaml` default to `hello@example.invalid`.

### Honest claims (read before you sell anything below)

What the repository has actually measured (`docs/acceptance.md`, evidence in `reports/`): a warning-free production build; all 41 variants passing axe WCAG A/AA in both themes at 320/390/600/900/1200 px; one H1 and no horizontal overflow per route; the CSS/JS budgets above; four presets building at root and `/client/` subpaths.

What is **not** measured and is yours to prove per project: current Lighthouse scores (the old demo's 100s are historical, not inherited), hosted TTFB, CO₂ figures, screen-reader and physical-device acceptance, and live form receipt. Several plays below are sold on numbers — measure the actual site first:

```sh
npm run check:browser                                              # axe + H1 + overflow + CSP (serves public/ itself)
python3 -m http.server 14722 --bind 127.0.0.1 --directory public   # serve production output for Lighthouse
npm run audit -- http://127.0.0.1:14722/                           # Lighthouse thresholds
```

---

## Table of Contents

1. [Core Agency & Client Delivery Plays (#1–#15)](#1-core-agency--client-delivery-plays)
2. [Vertical & Niche Industry Presets (#16–#35)](#2-vertical--niche-industry-presets)
3. [Performance, Accessibility & Green-Web Arbitrage (#36–#50)](#3-performance-accessibility--green-web-arbitrage)
4. [Digital Products, Themes & Boilerplates (#51–#65)](#4-digital-products-themes--boilerplates)
5. [Lead Generation, Directories & Local SEO (#66–#78)](#5-lead-generation-directories--local-seo)
6. [Interactive Sales & Discovery Closing Tools (#79–#88)](#6-interactive-sales--discovery-closing-tools)
7. [Creative Experiments, Passion Projects & Just for Fun (#89–#101)](#7-creative-experiments-passion-projects--just-for-fun)
8. [Appendix: the eight edits behind all 101](#appendix-the-eight-edits-behind-all-101)

---

## 1. Core Agency & Client Delivery Plays

**1. The "Site in a Day" sprint** — fixed fee, 24-hour turnaround.
- `python3 scripts/new_site.py ../client-name --name "Client Name" --preset local-service`, then `cd ../client-name && python3 scripts/setup.py`.
- Keep the shipped composition. Rewrite only the `sections` blocks in `data/presets/local-service.json` and set `theme.accent`, `email`, `address`, `hours`, `location` in `data/site.yaml`.
- Sequence: `factory.py` → `build.py` → `check_site.py` → walk the going-live list. The five disabled-by-default items are your pre-flight checklist, not obstacles.

**2. The "sculpting" discovery retainer** — a paid workshop instead of free mockups.
- Run the master with `workshop: true` in `data/factory.json` and open `/site-kit/` on the call.
- Decide the section list live, write it straight into `pages.home.sections` as `{ "module": …, "variant": …, "content": … }` entries, rebuild between rounds (~seconds), and refresh the tab.
- Leave with an agreed array. That array *is* the scope document.

**3. The living style guide as a paid deliverable.**
- `/site-kit/style-guide/` renders from the client's own `data/site.yaml` — palette, type scale, buttons, states, spacing.
- It only exists while `workshop: true`; client copies are scaffolded with `workshop: false` and no `site-kit/` tree. To hand one over, build it in the master with the client's `theme` values and export the HTML, or set `workshop: true` in their copy for the review build and back to `false` before publication.

**4. The "anti-bloat" WordPress rescue.**
- Inventory their pages, then map each one onto a preset page plus a section stack. Most brochure sites are `hero` + `services` + `about` + `process` + `faq` + `contact`.
- Move body copy into `sections`; move anything long-form into `content/<page>/<slug>.md` Markdown bodies (front matter: `title`, unique `description`, `heading`, `intro`).
- Their images go in `assets/images/`; reference as `images/<file>.png` and Hugo emits WebP srcsets with fallbacks.

**5. No-code / low-code overhauls** — Squarespace and Wix escapes.
- Rebuild the visual hierarchy with variants rather than custom CSS: `hero/centered` for statement pages, `bento/mosaic` for dense feature clusters, `features/split` for alternating rows.
- Measure before and after with `npm run audit` against the served `public/` directory so the pitch rests on two real numbers, not one claimed one.

**6. Quarterly content-refresh retainers.**
- Everything a retainer touches is text in one file: `sections` in the preset JSON (headings, cards, FAQs, pricing bullets) plus `content/work/*.md` for case studies.
- The contact form's service choices are the preset's `services` items, so they follow the Services page automatically. Keep `data/contact.yaml` (budget choices) in step with any published prices.
- Bill the gate run, not the edit: `factory.py` → `build.py` → `check_site.py` catches a broken link or a 60-character title before the client sees it.

**7. Teaser → full site, phased.**
- Launch with two entries in `pages.home.sections`: `hero/compact` and `contact/compact`.
- Each phase appends one entry and one `sections` block. Nothing earlier changes, so every phase is a two-minute diff.

**8. Subpath multi-site brand network.**
- Build each brand into its own directory: `python3 scripts/build.py --destination ../network/brand-a --base-url https://example.com/brand-a/`.
- Subpath builds are covered by `scripts/test_factory.py` (root and `/client/`). `check_site.py` verifies no reference escapes the base path.
- Never point `--destination` at a source directory, and use an empty destination per brand.

**9. Emergency rebuilds for hacked sites.**
- Pull surviving copy from the Internet Archive, drop it into a fresh `new_site.py` copy, and publish the four core pages first.
- Static output has no database and no admin surface. The contact form is the only dynamic path, and it stays disabled until you wire a real backend.

**10. The minimum viable rebrand.**
- Edit `theme.*` (ink, paper, mist, line, accent, accent_text, link, muted, plus the six `dark_*` values) and `font.family`/`font.file` in `data/site.yaml`, then rebuild.
- A valid hex is not an accessibility result: re-run `npm run check:browser` after any palette change — axe checks contrast in both themes.

**11. White-label for design boutiques.**
- Take their Figma frames and express them as variant choices. Map the 41 variants onto their layouts before quoting; anything unmappable is either a token change or genuinely custom work.
- Give them `/site-kit/` as the shared vocabulary so review comments arrive as "use `timeline/cards` here".

**12. The "de-CMS" downsizing service.**
- Deliverable is a directory of HTML, CSS, WebP, and one WOFF2. No PHP, no database, no plugin updates.
- Ship `static/fonts/OFL.txt` with the font. It is a license requirement, not a nicety.

**13. Subcontractor team expansion.**
- The whole job for a junior is: edit strings in one JSON file, obey the ten validation rules, run three commands.
- Onboarding doc is this file's "Read this first" plus `docs/factory-guide.md`. Their first task should be a deliberate mistake (misordered hero) so they see `factory.py` catch it.

**14. Speed audits with credited fixes.**
- Audit with `npm run audit -- <their URL>`; the report lands in `reports/`.
- State the offer against *measured* numbers only. The repo's thresholds (Performance ≥95, Accessibility 100, LCP <1.5 s, CLS <0.05, home <150 KB / ≤10 requests) are what the check enforces on your build — verify them on the finished client site before guaranteeing anything.

**15. Fixed-price niche packages.**
- One package = one preset + one frozen section stack + a fixed content quota (e.g. 6 services, 8 FAQs, 3 process steps).
- Keep the quota in the package copy and in the JSON. Over-quota content is a change order, and the array makes that visible.

---

## 2. Vertical & Niche Industry Presets

Each recipe below gives a **start**, a **home stack**, and the **edits**. Reading them:

- Modules outside the preset's shipped stack need a new block under `sections` — copy a valid one from the master's `data/examples.json` (client copies delete that file at scaffold time, so copy it out of the master while you have it).
- `work`, `pricing`, and `comparison` live on the `agency` preset. Adding them elsewhere = add the page key + `content/<page>/_index.md` + the sections (Appendix recipe 2).
- Regulated verticals (legal, medical, financial, veterinary) ship with sample notices for a reason. Claims, credentials, and disclaimers need the client's own sign-off before publication.

**16. Boutique architecture & interior design studio**
- Start `--preset agency`, tone `clay` (set `theme.accent` to `#edb08e`).
- Home: `hero/split` (art `factory` → swap to `tiles`) → `work/gallery` → `bento/mosaic` → `about/editorial` → `cta/quiet`.
- Photography goes in `assets/images/`; each `work` item takes `title`, `text`, `image`, `url` pointing at a `content/work/<slug>.md` case page.

**17. General contractor & custom home builder**
- Start `--preset contractor`.
- Home: keep the shipped stack, then insert `timeline/cards` (project phases, `phase` field per item) before `areas/cards` and `before-after/panels` after it.
- Credentials are not a module: use `features/grid` with `bullets[]` for licenses and insurance, or `logos/inline` for association marks (needs a `notice`).

**18. High-end independent consultant**
- Start `--preset consultant` (tone `sage`, hero `centered`, art `orbit`).
- Home: `hero/centered` → `about/editorial` → `services/cards` → `process/steps` → `resources/cards` → `cta/quiet`.
- Single-conversation CTA: point both `hero.action.url` and `cta.action.url` at `/contact/` and delete every other action. One offer, one path.

**19. Local trades & emergency services**
- Start `--preset local-service`.
- Home: `hero/split` → `services/cards` → `areas/cards` → `process/steps` → `faq/open` → `contact/compact`.
- Phone is not a module link (rule 6 rejects `tel:`). Put the number in `hero.note` and in `contact.items`, and add a `tel:` anchor in a Markdown body if you want it clickable.

**20. Boutique law firm / specialty attorney**
- Start `--preset consultant`, tone `blue`, hero `compact` everywhere for a typographic feel.
- Home: `hero/centered` → `features/split` (practice areas, one `bullets[]` list each) → `about/editorial` → `faq/accordion` → `cta/quiet`.
- Keep a visible disclaimer: put it in each section's `notice` where allowed, and in `data/site.yaml`'s `notice` for the footer.

**21. Specialty medical / dental practice**
- Start `--preset local-service`.
- Home: `hero/split` → `services/cards` → `process/steps` (patient preparation) → `team/cards` → `faq/accordion` → `contact/panel`.
- Do not collect patient detail through the contact form. Keep `formEnabled = false` and publish a phone number until a compliant intake path exists.

**22. Artisan coffee roaster & tasting room**
- Start `--preset contractor` (clay reads as earthy).
- Home: `hero/split` → `timeline/vertical` (origin/harvest/roast, `phase` per item) → `pricing/cards` (subscription tiers, `value` + `bullets[]`, `notice` required) → `contact/panel`.
- Wholesale enquiries: add the option to the preset's `services` items so it appears in the form.

**23. Craft brewery & taproom**
- Start `--preset local-service`.
- Home: `hero/split` → `bento/mosaic` (events; `badge` for the night, `span: large` for the headliner) → `services/rows` (tap list) → `areas/cards` (hours/location) → `cta/band`.
- Tap list changes weekly: it is one `items` array, so hand the client that file and nothing else.

**24. Independent financial planner / wealth advisor**
- Start `--preset consultant`.
- Home: `hero/centered` → `features/grid` (fiduciary pledge, credentials) → `pricing/rows` (fee transparency) → `process/steps` → `faq/accordion` → `cta/quiet`.
- Fee tables must carry a real `notice`. Replace the sample text; illustrative pricing next to regulated advice is a liability, not a placeholder.

**25. Commercial real estate development firm**
- Start `--preset agency` (keeps the `work` page for properties).
- Home: `hero/split` → `work/gallery` (properties) → `timeline/cards` (zoning → permit → build → lease) → `stats/strip` (`notice` required) → `contact/panel`.
- Each property becomes `content/work/<slug>.md`. That layout expects `image`, `alt`, `metric_label`, and all six `metrics` fields — fill them or switch the page to a plain `content/<section>/<slug>.md`.

**26. Boutique fitness studio / CrossFit box**
- Start `--preset local-service`.
- Home: `hero/split` → `comparison/table` (class schedule: `scope` = time, `best` = level) → `team/cards` (coaches, `initials`) → `pricing/cards` (memberships) → `cta/band`.
- `comparison` needs its own page on this preset or a slot on home; either way add the sections block with `notice`, `scope`, and `best`.

**27. High-end wedding / event venue**
- Start `--preset agency`.
- Home: `hero/split` (full-bleed image via a `work` item or hero art) → `bento/mosaic` (spaces) → `pricing/cards` (packages) → `faq/accordion` (availability) → `contact/panel`.
- Tour booking is a contact path, not a calendar. Add "Book a tour" to the preset's `services` items and keep expectations in `contact.items`.

**28. Specialty accounting & tax practice**
- Start `--preset consultant`.
- Home: `hero/compact` → `services/rows` → `process/steps` (document checklist) → `resources/cards` (deadline guides, `url` to local pages only) → `faq/accordion`.
- Seasonal notices: `sections.<key>.notice` renders as a visible band. Update it each quarter rather than adding a module.

**29. Landscape design & hardscaping**
- Start `--preset contractor`.
- Home: `hero/split` → `before-after/panels` (`notice` required) → `services/cards` (seasonal tiers) → `areas/cards` (radius) → `cta/band`.
- Before/after imagery belongs in `work` items or a Markdown body; the `before-after` module is copy-only (title + text).

**30. Fine furniture maker / bespoke craftsman**
- Start `--preset agency`.
- Home: `hero/split` → `about/editorial` (material provenance, use `body` + `aside`) → `process/steps` (commission path) → `work/gallery` → `cta/quiet`.
- `about` requires `title`, `intro`, **and** `body`; `aside` is the pull-quote slot.

**31. Executive search / headhunting firm**
- Start `--preset consultant`.
- Home: `hero/centered` → `features/split` (two audiences: candidates, employers) → `timeline/vertical` (retained search stages) → `faq/accordion` → `contact/compact`.
- Confidentiality: keep the form disabled and publish a direct address, or bind the Pages Function to a named recipient before enabling it.

**32. Independent software consultant / fractional CTO**
- Start `--preset consultant`.
- Home: `hero/centered` → `logos/inline` (stack badges, `notice` required) → `work/editorial` (case studies; needs a `work` page) → `pricing/rows` (retainers) → `cta/quiet`.
- ROI numbers in case studies: the shipped `metrics` fields are labelled illustrative. Replace with client-approved figures or delete the metric block.

**33. HVAC & energy efficiency auditor**
- Start `--preset local-service`.
- Home: `hero/split` → `services/cards` → `comparison/cards` (equipment options) → `process/steps` (diagnostic visit) → `areas/cards` → `contact/panel`.
- Rebate deadlines go in a section `notice` (there is no separate notice module — `notice` is a field on `pricing`, `areas`, `testimonials`, `stats`, `contact`, `comparison`, `before-after`, `logos`, `work`, `team`).

**34. Specialty veterinary clinic**
- Start `--preset local-service`.
- Home: `hero/split` (emergency hours in `note`) → `services/cards` → `team/cards` → `faq/open` → `contact/panel`.
- Emergency information must be above the fold and must not depend on JavaScript. It does not here — only the contact page ships script.

**35. Boutique catering & private chef**
- Start `--preset contractor`.
- Home: `hero/split` → `comparison/table` (sample menus: `scope` = courses, `best` = occasion) → `pricing/cards` (per-head tiers) → `faq/accordion` (dietary) → `contact/panel`.
- Dietary requirements belong in the form's free-text field; keep the preset's `services` titles short.

---

## 3. Performance, Accessibility & Green-Web Arbitrage

Every play here sells a number. Generate the number on the finished client build before it appears in a contract.

**36. The "perfect 100" Lighthouse offer**
- Measure: serve `public/` with `python3 -m http.server 14722 --bind 127.0.0.1 --directory public`, then `npm run audit -- http://127.0.0.1:14722/`. Reports land in `reports/`.
- `npm run audit` enforces Performance ≥95, Accessibility 100, LCP <1.5 s, CLS <0.05, home <150 KB and ≤10 requests, and exits nonzero on failure.
- Guarantee against *your* hosted measurement, not the repo's history: `docs/acceptance.md` states the old demo's 100s are historical and not inherited.

**37. Green web / low-carbon positioning**
- What you can show: the transferred bytes. CSS is ~5.5 KB gzipped, images are WebP with fallbacks, fonts are one self-hosted variable WOFF2, and only the contact page loads script.
- What you cannot show from this repo: grams of CO₂. Feed your measured page weight into a third-party calculator and cite that tool, with the host's energy mix as the variable you do not control.

**38. Accessibility (ADA / Section 508) retrofits**
- Evidence you can run: `PREVIEW_URL=http://127.0.0.1:14722/ npm run check:browser` — axe WCAG A/AA, one H1, `noindex`, light and dark, widths 320/600/900/1200. All 41 variants pass in the master (`reports/factory-workshop-checks.json`).
- Scope honestly: automated checks do not establish conformance. Keyboard walkthrough, screen-reader passes, and zoom/reflow testing are separate manual line items.
- Re-run after every color or font change; contrast is a token, and tokens move.

**39. Rural & low-bandwidth optimization**
- Budget check already enforces small bundles; keep total payload down by limiting `work` items and using `bento/compact` over `mosaic`.
- Verify the request count in the Lighthouse report (home ≤10 requests) and test on a throttled profile in DevTools before quoting field performance.

**40. Mobile-first conversions for field services**
- `hero/split` collapses on narrow widths; overflow is checked at 320 px, so a phone-first layout is the default, not a retrofit.
- Put the phone number in `hero.note` and the first `contact.items` entry, and keep home to four sections so the CTA is one thumb-scroll away.

**41. Battery-saving dark mode**
- `<meta name="color-scheme" content="light dark">` ships in `head.html`; the palette's `dark_*` tokens in `data/site.yaml` drive the dark theme. No toggle, no flash, no JavaScript.
- Verify both modes after any palette edit — `check:browser` runs axe twice, once per mode.

**42. Core Web Vitals arbitrage**
- Pitch: their framework ships a JS bundle; this ships one stylesheet under 20 KB gzipped and script on a single page.
- Back it with two Lighthouse runs (theirs, yours) captured the same day on the same connection, saved to `reports/`.

**43. Zero-JavaScript resilience**
- Demonstrable: the catalog, style guide, FAQ (`<details>`), and disabled contact page all work with JavaScript off — verified by `node scripts/check_workshop.cjs`.
- With forms enabled, submission is a same-origin HTML POST with a honeypot; the optional script only adds status messages and input retention. No-JS error rendering depends on the host.

**44. Sub-second TTFB static hosting**
- Any static host serves the output. `wrangler.toml` is a pinned Cloudflare Pages recipe (Hugo 0.166.0, Dart Sass 1.104.1) and nothing more — it does not deploy or connect an account. The form endpoint needs Pages Functions; static-only hosts serve the pages but not `/api/contact`.
- `static/_headers` is Cloudflare/Netlify-style. On other hosts you must re-create cache, compression, HTTPS, and CSP settings, then verify them at the host.

**45. Font-privacy / GDPR compliance**
- The font is local: `static/fonts/inter-latin-variable.woff2`, preloaded, referenced by `font.file` in `data/site.yaml`. No third-party font request exists to block.
- Ship `static/fonts/OFL.txt`. If you swap fonts, swap the license file too and re-run contrast checks.

**46. Bandwidth bill reduction**
- The measurable deliverable is bytes per page view before and after. Take "before" from their host's analytics or a Lighthouse run of the live site; take "after" from your build's Lighthouse report.
- Multiply by their actual monthly page views. Do not reuse someone else's ratio.

**47. Sustainable business / CSR award entries**
- Assemble: measured page weight, request count, request origins (all first-party except any embed you added), and the accessibility report.
- `reports/` already stores browser-check JSON and screenshots — that directory is the evidence packet.

**48. Print-optimized brochure replacement**
- The HTML is semantic and single-column at narrow widths, which usually prints cleanly. There is **no dedicated print stylesheet** in `assets/scss/` yet.
- If print matters, add a `@media print` block to `assets/scss/main.scss` and check the CSS budget afterwards (20 KB gzipped per bundle).

**49. Offline field companion sites**
- Not built in: there is no service worker in this repo. You would add one under `static/` and register it — which means adding your first non-contact JavaScript.
- Budget is 5,000 bytes gzipped per emitted JS bundle, and `check_site.py` enforces it. Keep the worker tiny or the gate fails.

**50. Host-independent resiliency**
- The deliverable is `public/` plus the source tree. No runtime, no database, no vendor API.
- One caveat to state: URLs follow `baseURL`, so moving to a different path means one rebuild (`--base-url`), not a hand-edit.

---

## 4. Digital Products, Themes & Boilerplates

Before selling anything derived from this tree: **there is no `LICENSE` file in the repository yet**, and `package.json` is marked `private`. Add the license you intend to grant before the first sale. The only third-party license currently bundled is the font's `static/fonts/OFL.txt`, which must travel with any copy.

**51. Niche industry theme marketplace**
- A sellable "theme" here is small: one `data/presets/<slug>.json`, matching `theme` values for `data/site.yaml`, any `assets/images/`, plus a one-page install note.
- Test each theme by dropping it into a clean `new_site.py` copy and running the three gates. A preset that fails `factory.py` is a refund.
- Add your slug to the `--preset` choices in `scripts/new_site.py` (two places: the `create()` guard and the argparse `choices`) if buyers should scaffold with it.

**52. The "freelancer OS" starter kit**
- Bundle the tree with the onboarding material that is missing from it: proposal template, content-collection checklist, handover script.
- `docs/starter-guide.md` is the client-facing handover sequence and `docs/factory-guide.md` the editing guide — both already ship into every copy. Write yours around them, not over them.

**53. Micro-SaaS marketing front**
- Home: `hero/centered` → `features/split` → `bento/mosaic` → `pricing/cards` → `faq/accordion` → `cta/band`.
- Docs are Markdown subpages (`content/docs/<slug>.md` with `title`, unique `description`, `heading`, `intro`) plus `"docs"` in the preset's `pages`.
- App links are external, so they go in Markdown bodies, not module items (rule 6).

**54. Subscription design-system club**
- A month's release = one new entry in `data/modules.json`, its render branch in `layouts/partials/factory/module.html`, styles in `assets/scss/pages/_factory.scss`, and an example in `data/examples.json`.
- Ship each release only after `node scripts/check_workshop.cjs` passes: it axe-checks every variant in both themes at five widths.

**55. Component snippet packs**
- The Sass is already modular under `assets/scss/` (`abstracts/`, `base/`, `components/`, `layout/`, `pages/`), consumed via `@use` from `main.scss`.
- Note for buyers: colors arrive as Sass variables injected by Hugo from `data/site.yaml` (`hugo:vars`). A standalone drop needs those values inlined as CSS custom properties.

**56. Static site starter course**
- The curriculum writes itself from the pipeline: `factory.json` → preset → `modules.json` → `compose.html` → checks.
- Best single lesson: break something on purpose (unknown variant, second hero, external URL in a module) and watch `factory.py` name the file and the rule.

**57. Figma-to-factory design bridge**
- Mirror exactly the 20 families and 41 variants from the table above; name Figma components `module/variant` so a handoff comment maps to a JSON edit.
- Mirror tokens from `data/site.yaml` `theme` and the style guide at `/site-kit/style-guide/`. Spacing and breakpoints stay developer-owned Sass tokens — mark them non-negotiable in the kit.

**58. Lead-magnet bundles**
- Gate a zip of one preset + theme behind an email form. Your own site's form posts to its own Pages Function, so extend that endpoint rather than adding a provider.
- Keep the giveaway a preset, not the engine, if you plan to sell the engine later.

**59. Notion-to-factory workflow toolkit**
- Nothing ships for this; you write it. Target shape: a script that emits a preset's `sections` object as JSON.
- Make the script's last step `python3 scripts/factory.py`, so a bad export fails before a build. Match the required fields per module from the catalog table.

**60. Static store with hosted checkout (Snipcart / Stripe)**
- `pricing/cards` has no link fields, and module URLs must be local paths. Put the buy button in a Markdown subpage per product and link `pricing` items to that page.
- Third-party checkout scripts blow the 5 KB gzipped JS budget in `check_site.py`. Load them from the vendor's domain (external refs are not size-checked) or raise the budget deliberately — do not silently delete the check.

**61. Membership landing hub**
- Public marketing pages here; gated content stays in the membership provider. Link out from a Markdown body.
- Login is an external URL, so it cannot live in `hero.action`. Either add a Markdown body link or extend the link validator in `scripts/factory.py`.

**62. Newsletter landing page collection**
- Minimum viable page: `hero/centered` + `cta/quiet`, two sections total, two `sections` blocks.
- Signup forms are provider-hosted embeds; keep the built-in form disabled so there is exactly one submit path.

**63. GitHub Sponsors reward tiers**
- Tier = early access to a preset or module family. The repo is already structured so a family is a self-contained set of files (see #54).
- Publish the tier list as `pricing/cards` on your own site; `notice` is required, so use it to state what a tier does not include.

**64. Affiliate comparison theme**
- Home: `hero/compact` → `comparison/table` → `features/grid` → `faq/accordion` → `cta/band`.
- Affiliate links are external: each compared product needs a Markdown subpage that holds the outbound link, with the `comparison` item's local `url` pointing there. Disclosure text goes in the module's `notice`.

**65. "Agency in a box" white-label license**
- What you are licensing: the layouts, Sass, and Python helpers. What you are not: the font (OFL, separate terms) and any imagery you did not create.
- Add `LICENSE`, decide whether resale includes the workshop (`workshop: true` in `data/factory.json`), and note that copies scaffolded by `new_site.py` deliberately exclude the workshop, other presets, and historical acceptance evidence.

---

## 5. Lead Generation, Directories & Local SEO

**Directories hit rule 6 head-on**: module content cannot hold external links. Every play in this section therefore uses the same two-layer shape —

1. A composition page (`content/<section>/_index.md`) that renders modules and links *internally* to entry pages.
2. One Markdown entry page per listing: `content/<section>/<slug>.md` with front matter `title`, a **unique** `description` under 155 characters, `heading`, `intro`, and a body free to hold outbound links.

Plus: `noindex` ships on every page and `check_site.py` requires it, so an SEO play is not live until you have done the going-live list.

**66. Hyper-local service directories**
- Composition: `hero/compact` → `resources/cards` (one card per listing, local `url`) → `faq/open` → `contact/panel`.
- Verification badges: `logos/grid` with a `notice` stating what you did and did not verify (text marks, not uploaded logos — see #78).

**67. B2B vendor comparison hubs**
- `comparison/table` for the matrix (every item needs `scope` and `best`) plus `features/split` for the long-form argument.
- Keep each comparison page's title under 60 characters including the site name suffix — matrices generate long titles and that check bites here first.

**68. Local city guide**
- `bento/mosaic` with `badge` as the category and `span: large` for the featured listing.
- Map links are external: put them in the entry page bodies.

**69. "Rank and rent" local SEO assets**
- Build one `local-service` copy per niche/city. `new_site.py` refuses to overwrite, so each is a separate directory.
- Swap the rented lead destination by changing one form recipient — keep `formEnabled` off until a real recipient exists, and verify actual receipt rather than trusting the success page.

**70. Programmatic case study library**
- Duplicate `content/work/fieldwork.md`; every copy needs a unique filename, `title`, `description`, `image`, `alt`, `metric_label`, and all six `metrics` values.
- `check_site.py` fails on duplicate titles or descriptions, which is exactly the guard you want when generating at volume.
- Keep the sample disclaimer (`case_notice` in `data/site.yaml`) until the numbers are real.

**71. Curated niche job board**
- Listing index: `resources/rows`; each role is an entry page. Application links are external, so body-level.
- Expiring roles: delete the entry page and its `resources` item, then rebuild — `build.py` removes previously generated pages via its build manifest.

**72. Trade accreditation index**
- `comparison/cards` per trade, `logos/inline` for issuing bodies, and a hard `notice` describing your verification date and method.
- This is a claims-heavy format. Do not publish a license status you have not checked yourself.

**73. Regional real estate directory**
- Start `--preset agency` for the `work` page, or add a `listings` page on any preset.
- Facets (district, county) are separate pages, each with its own `_index.md` metadata; there is no taxonomy layer (`taxonomy` and `term` kinds are disabled in `hugo.toml`).

**74. Wedding vendor collective**
- `team/cards` works as the vendor roster (`initials` for those without a logo); each vendor gets an entry page with their outbound link.
- One shared `contact` module routes enquiries to the collective, so there is a single form to keep honest.

**75. Local emergency preparedness resource**
- Fewest possible sections: `hero/split` with the critical number in `note`, then `resources/rows`, then `faq/open`.
- This page must work with JavaScript off and on a bad connection — which it does, since only the contact page ships script. Do not add embeds here.

**76. Restaurant week guide**
- `comparison/table` for menus (`scope` = price, `best` = cuisine), `bento/compact` for the day-by-day grid.
- Reservation links are external: entry page per restaurant.

**77. Conference speaker & agenda hub**
- `timeline/vertical` for the agenda (`phase` = time slot), `team/cards` for speakers, `pricing/cards` for ticket tiers.
- One `_index.md` composition plus a speaker entry page each keeps every bio's meta description unique.

**78. Micro-sponsorship marketplace**
- `pricing/rows` for sponsor tiers (`value` + `bullets[]`, `notice` required), `logos/grid` for current sponsors.
- `logos` renders sponsor **names and text**, not image files — only the `work` module renders item images. Real logo images need either a `work`-style gallery or a Markdown body.

---

## 6. Interactive Sales & Discovery Closing Tools

Every play here runs on the master copy with `"workshop": true` in `data/factory.json`. Rehearse the rebuild-and-refresh rhythm once before doing it in front of a prospect: `--serve` does not live-reload.

**79. The "live wireframe" pitch**
- Two terminals: one running `python3 scripts/build.py && python3 scripts/build.py --serve --port 1313`, one editing the preset JSON.
- Open `/site-kit/` to browse, then the composition itself at `/` to show the real page. Edit → `Ctrl-C` → rebuild → refresh takes seconds.
- Have `factory.py` handy. When it rejects something, say why out loud: it is the guardrail you are selling.

**80. The "before & after" tear-down**
- Paste their existing copy into the preset's `sections`, build, and put the two sites side by side.
- Then the numbers: Lighthouse their live URL and your local `public/` build in the same sitting (see #36). Same day, same machine, same connection, or the comparison is not one.

**81. Menu-pricing your modules**
- Your menu is the catalog table: 20 families, 41 variants. Price per family, not per hour.
- Put honest floors on the ones with real cost: modules requiring a `notice` need approved copy, and `work` needs a `work` page plus imagery.

**82. The "instant rebrand" demo**
- Before the call: their hex values into `theme.accent`, `theme.link`, and the `dark_*` pairs in `data/site.yaml`; their name into `name` and `wordmark`.
- Rebuild and run `npm run check:browser` first — reveal a palette that already passes contrast, not one you have to apologize for.

**83. A/B content prototyping**
- Duplicate the preset file (`cp data/presets/agency.json data/presets/agency-proof.json`), reorder `pages.home.sections` in the copy, and flip `preset` in `data/factory.json` between builds.
- Both variants must pass validation, so the comparison is between two real pages.

**84. Client self-editing sandbox**
- Hand over a `new_site.py` copy plus three commands. They can only edit text in one JSON file and Markdown bodies; styles and layout are untouched by that surface.
- Tell them `factory.py` is the undo button's friend: it names the file, key, and rule for any mistake.

**85. The "no hidden costs" hosting comparison**
- Concrete list: static hosting, a domain, and optional form handling. No CMS license, no plugin subscriptions, no PHP host.
- Be exact about what is not implemented: form delivery is a Cloudflare Pages Function only. On another host, budget for a backend.

**86. Stakeholder alignment workshops**
- Project `/site-kit/` and make each department argue for a specific module on a specific page. The output is an ordered array, which is harder to fudge than a wishlist.
- Cap home at five or six sections in front of them; the shipped presets all do, which makes the cap look like a standard rather than a preference.

**87. The post-launch upsell engine**
- An MVP typically uses 5–7 of the 20 families. Review the unused ones each quarter — `bento`, `timeline`, `features`, `logos`, `stats`, `testimonials`, `comparison`, `before-after` are the usual leftovers.
- Each is one `sections` block, one array entry, one gate run. Quote it that way.

**88. The "take it with you" guarantee**
- Show the tree: Hugo templates, standard Sass, standard-library Python, JSON and YAML data, one WOFF2.
- Name the two dependencies honestly — pinned Hugo Extended 0.166.0 and Dart Sass 1.104.1 — and that the optional Node tooling is checks only.

---

## 7. Creative Experiments, Passion Projects & Just for Fun

These are the fastest way to learn the system; nobody is waiting on them. All of them still start with `new_site.py` into a directory outside this project.

**89. The living interactive resume**
- `--preset consultant`. Home: `hero/centered` → `timeline/vertical` (roles, `phase` = years) → `bento/mosaic` (skills, `badge` per area) → `work/gallery` → `contact/compact`.
- `work` needs a `work` page: use `--preset agency` instead, or add the page (Appendix recipe 2).

**90. Indie game teaser & devlog**
- `--preset agency`, dark-leaning palette via the `dark_*` tokens.
- Home: `hero/split` (art `orbit`) → `bento/mosaic` (features) → `timeline/cards` (lore or roadmap) → `faq/accordion` → `cta/band`. Devlog entries are `content/devlog/<slug>.md` plus `"devlog"` in `pages`.

**91. Personal archive & memory box**
- `timeline/vertical` for the family line, `work/gallery` for photographs (the only module that renders images — and edit its hardcoded `alt` text, see the rules).
- Keep it unpublished: `noindex` and `example.invalid` are already the defaults, so doing nothing keeps it private.

**92. Podcast companion site**
- `--preset consultant`. Episodes are Markdown subpages; transcripts go straight in the body.
- Audio players are external embeds, so body-level, not module content. Watch the JS budget if the player is self-hosted.

**93. Book / novel launchpad**
- Home: `hero/split` → `about/editorial` (the pitch, `body` + `aside`) → `testimonials/featured` (praise, `notice` required) → `faq/accordion` (glossary) → `cta/band`.
- Buy links are external: one Markdown page for retailers, linked from `cta.action.url`.

**94. Neighborhood tool library**
- `--preset local-service`. `comparison/table` as the catalog (`scope` = condition, `best` = job), `areas/cards` for pickup points.
- Availability is text in an `items` array — good enough for a page someone edits weekly, and no backend to run.

**95. Personal coffee tasting journal**
- `comparison/table` per brew (`scope` = ratio, `best` = roast), `bento/compact` for tasting notes with `badge` as the origin.
- One entry page per bag if you want long notes; the index stays a single composition.

**96. Micro-hobby hall of fame**
- `bento/mosaic` with `span: large` for the crown jewel, `comparison/cards` for spec sheets, `work/gallery` for photos.
- Photography needs `--preset agency` (or an added `work` page) since that is where the gallery lives.

**97. Indie film festival guide**
- `timeline/vertical` (screenings, `phase` = time), `team/cards` (directors), `pricing/cards` (tickets, `notice` required).
- Trailers are external embeds: one film page each, links in the body.

**98. Wedding / anniversary portal**
- `--preset contractor` for the warm clay accent. Home: `hero/split` → `timeline/vertical` (the story) → `faq/accordion` (dress code, travel) → `contact/panel` (RSVP instructions).
- RSVP by form requires the Pages Function bindings and a real recipient. Until then, publish an address and keep `formEnabled = false`.

**99. Open-source project showcase**
- `hero/centered` → `features/grid` → `comparison/table` (feature matrix) → `faq/accordion` → `cta/quiet`.
- Install commands go in a Markdown body (fenced code blocks render); repo links are external, so body-level too.

**100. Travel / expedition log**
- `timeline/cards` for stages (`phase` = day or leg), `resources/rows` for gear lists, `stats/strip` for distances (`notice` required).
- One Markdown page per leg keeps every meta description unique, which `check_site.py` insists on.

**101. The "anti-portfolio" of failed experiments**
- `before-after/stacked` for what you expected versus what happened (`notice` required — use it for the joke), `stats/cards` for the damage, `timeline/vertical` for the chronology.
- Fitting first build: it uses four modules the default presets leave out, so it teaches the `sections`-plus-array edit in one sitting.

---

## Appendix: the eight edits behind all 101

### 1. Add a section to a page

In `data/presets/<preset>.json`, add one array entry and one content block:

```json
"pages": { "home": { "sections": [
  { "module": "hero",     "variant": "split",  "content": "hero" },
  { "module": "timeline",  "variant": "cards",  "content": "milestones" }
] } },
"sections": {
  "milestones": {
    "label": "How it goes",
    "title": "A dependable path from brief to launch.",
    "intro": "What happens, and when.",
    "items": [
      { "title": "Discovery", "text": "Constraints, audience, content inventory.", "phase": "Week 1" },
      { "title": "Build",     "text": "Agreed sections, reviewed on real pages.",  "phase": "Week 2" }
    ]
  }
}
```

Then `python3 scripts/factory.py`. Copy a correct starting block for any module from `data/examples.json`.

### 2. Add a page

```sh
mkdir -p content/pricing
cat > content/pricing/_index.md <<'JSON'
{
  "title": "Scope & pricing",
  "description": "Compare engagements. Real fees and scope require a proposal."
}
JSON
```

Add a matching `pages.pricing` object with `title`, `description`, and `sections` (first entry a `hero`), then add its content blocks. A page directory absent from `pages` is dropped at build time.

### 3. Add a plain Markdown subpage (for outbound links, docs, listings)

```sh
cat > content/services/retainers.md <<'MD'
---
title: "Retainers"
description: "How ongoing work is scoped, reviewed, and billed."
heading: "Ongoing work, clearly scoped."
intro: "What a monthly arrangement covers."
---
External links are fine here: [an example](https://example.com/).
MD
```

`description` must be unique across the site and under 155 characters.

### 4. Rebrand

`data/site.yaml`: `name`, `wordmark`, `tagline`, `description`, `email`, `address`, `hours`, `location`, `theme.*` (six-digit hex), `font.family` / `font.file`. Rebuild, then re-run `npm run check:browser` for contrast in both themes.

### 5. Switch or add a preset

`data/factory.json` → `{ "preset": "<slug>", "workshop": true|false }`. A new slug needs a `data/presets/<slug>.json` with a valid `tone` (`yellow`, `clay`, `sage`, `blue`), and — to be scaffoldable — adding to both `--preset` lists in `scripts/new_site.py`.

### 6. Add a case study

Copy `content/work/fieldwork.md`; change the filename and every one of `title`, `description`, `heading`, `intro`, `industry`, `image`, `alt`, `weight`, `metric_label`, and all six `metrics` fields. Image into `assets/images/`.

### 7. Build somewhere else / under a subpath

```sh
python3 scripts/build.py --destination ../out/brand-a --base-url https://example.com/brand-a/
```

Use an empty destination. Never target a source directory. Previously generated files that were hand-edited, or untracked HTML in the destination, stop the build on purpose.

### 8. The gates, in order

```sh
python3 scripts/factory.py       # configuration
python3 scripts/build.py         # build + publish verified output
python3 scripts/check_site.py    # generated output
python3 scripts/test_factory.py  # reordering, omission, failure paths
python3 scripts/test_starter.py  # client copy, branding, subpath, broken-link detection
# optional, Node:
npm run check:browser                          # serves public/ itself
python3 scripts/build.py --workshop && node scripts/check_workshop.cjs
python3 -m http.server 14722 --bind 127.0.0.1 --directory public
npm run audit -- http://127.0.0.1:14722/
```

Deployment, indexing, form delivery, and publication are owner-controlled and are not performed by any script here. See `docs/factory-guide.md` for the editing reference, `docs/acceptance.md` for measured evidence and its limits, and `roadmap.md` for what is planned but not built.

*Build fast. Run fast. Sculpt deliberately.*
