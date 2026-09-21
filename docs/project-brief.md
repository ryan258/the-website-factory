> Historical brief for the original five-page reference demo. The current factory contract is documented in README.md, docs/factory-guide.md, and roadmap.md.

# TheWebsiteFactory.com — Developer Project Brief

2026-09-21 · @Someone

## TL;DR

Build a **five-page**, very fast marketing site for a fictional web design company called TheWebsiteFactory.com.

- Tool: **Hugo** (a program that turns text files into a finished website).
- Styles: **Sass** (a way to write CSS, the styling language, with variables and reusable pieces).
- Tone of the words: serious and believable, like a real company.
- Look: clean and modern, with one bright accent color. The client did not pick a look, so this brief assumes it. It is easy to change (see Design system).
- The site is fictional. No real company, person, or brand may be copied.

## Goals, audience, and scope

The site must show that TheWebsiteFactory.com builds **fast** websites. The site itself must be fast, or the pitch fails.

**Goals**

1. Explain the company and its services in under 30 seconds of reading.
2. Prove speed with the site's own scores.
3. Move visitors to one action: the contact form.

**Audience**

- Small business owners who need a new site.
- Marketing managers who need a faster site.
- Both groups are busy. They skim. They often use a phone.

**In scope**

- Five pages: Home, Services, Work, Pricing, Contact.
- A full Hugo project with Sass styles.
- Sample content for every page (written by the developer from this brief).
- A working contact form.

**Out of scope**

- A blog.
- User accounts or a shopping cart.
- A content management system (a login screen for editing).
- Real client work. All case studies are made up and must say so.

## Tech stack and setup

Use **Hugo Extended**. The Extended version is required because it builds Sass. The standard version cannot.

| Tool | What it does | Requirement |
| --- | --- | --- |
| Hugo Extended | Builds the site from templates and content | Latest stable release. Pin the version in a `.hugo-version` file. |
| Dart Sass | Compiles Sass into CSS | Use Hugo's built-in Sass support. Do not add a separate build tool. |
| Git | Tracks changes | One repository. Clear commit messages. |
| Node.js | Optional, for testing tools only | Not needed to build the site. |

**Rules**

- No CSS framework (no Bootstrap, no Tailwind). Write all styles in Sass.
- No JavaScript framework (no React, no Vue).
- Use plain JavaScript only where needed. Keep the total under **5 KB** after compression.
- No third-party scripts. No analytics that set cookies.

**Commands the project must support**

1. `hugo server` starts a local preview with live reload.
2. `hugo --minify --gc` builds the final site into the `public/` folder.
3. The build must finish with **zero warnings**.

**Hugo pipes** (Hugo's built-in way to process files) handle the styles:

1. Compile Sass with `resources.Get` and `css.Sass`.
2. Minify the result.
3. Add a fingerprint (a unique code in the file name so browsers refresh it after changes).
4. Add the `integrity` attribute to the link tag.

Limit to know: Hugo Extended must be installed on the developer's computer. On Windows and Mac it is one download or one package manager command. The developer should confirm the version works before starting.

## Folder structure

Use this layout. Keep names exactly as shown so any Hugo developer can find things fast.

```
thewebsitefactory/
├── hugo.toml                 site settings
├── .hugo-version             pinned Hugo version
├── content/
│   ├── _index.md             Home
│   ├── services/_index.md
│   ├── work/_index.md
│   ├── work/*.md             one file per case study
│   ├── pricing/_index.md
│   └── contact/_index.md
├── data/
│   ├── services.yaml         list of services
│   ├── plans.yaml            pricing plans
│   └── faq.yaml              questions and answers
├── layouts/
│   ├── _default/baseof.html  the page shell
│   ├── _default/single.html
│   ├── index.html            Home template
│   ├── work/list.html
│   ├── work/single.html
│   └── partials/             header, footer, head, cards, form
├── assets/
│   ├── scss/                 all Sass (see Design system)
│   └── js/                   small scripts, if any
├── static/
│   ├── favicon.svg
│   └── fonts/                self-hosted font files
└── README.md                 setup and build steps
```

**Why data files matter:** services and prices live in `data/` files, not inside templates. A non-developer can then edit text without touching HTML.

## Design system

The look is **clean and modern** with one bright accent. All values below are starting points. The developer may adjust them if contrast rules (see Accessibility) still pass.

**Colors** (define once as Sass variables, then output as CSS custom properties)

| Name | Value | Use |
| --- | --- | --- |
| Ink | `#14181F` | Main text, dark sections |
| Paper | `#FFFFFF` | Page background |
| Mist | `#F3F5F7` | Alternate section background |
| Line | `#D8DDE3` | Borders |
| Accent | `#FFC400` | Buttons, highlights (safety yellow) |
| Accent text | `#14181F` | Text on yellow (never white on yellow) |
| Link | `#0A5CD6` | Text links |

Provide a dark mode that follows the visitor's device setting (`prefers-color-scheme`).

**Type**

- One font family, self-hosted, **variable font** (one file that holds many weights). Suggested: Inter or a similar open-license font.
- Use `font-display: swap` so text shows at once.
- Base size 18px. Scale: 1.25 ratio. Use `clamp()` so headings grow smoothly with screen size.
- Line height 1.6 for body text, 1.15 for headings.

**Spacing and layout**

- Spacing scale: 4, 8, 16, 24, 32, 48, 64, 96 pixels. Use only these.
- Content width: 1120px maximum. Reading width: 65 characters.
- Mobile first. Breakpoints: 600px, 900px, 1200px.
- Use CSS Grid and Flexbox. No floats.

**Sass architecture** (7-1 style, kept small)

```
assets/scss/
├── main.scss          imports everything, in order
├── abstracts/
│   ├── _variables.scss   colors, sizes, spacing
│   ├── _mixins.scss      breakpoints, focus ring
│   └── _functions.scss   rem conversion
├── base/
│   ├── _reset.scss
│   ├── _typography.scss
│   └── _root.scss        CSS custom properties, dark mode
├── layout/
│   ├── _container.scss
│   ├── _header.scss
│   └── _footer.scss
├── components/
│   ├── _button.scss
│   ├── _card.scss
│   ├── _form.scss
│   └── _pricing-table.scss
└── pages/
    └── _home.scss        only if needed
```

**Sass rules**

- Use `@use`, not `@import` (`@import` is deprecated).
- Nest no deeper than 3 levels.
- One mixin for breakpoints, used everywhere.
- Name classes with BEM (`block__element--modifier`), for example `card__title`.
- Final CSS after compression: **under 20 KB**.

## The five pages

Every page shares the same header and footer. Every page has one `h1`, a short intro, and one clear call to action (a button that asks the visitor to act).

### 1. Home (`/`)

Goal: explain the company and get a click to Contact.

1. **Hero.** Headline: "Websites built fast. Websites that run fast." Subtext: one sentence on what the company does. Two buttons: "Start a project" (main) and "See our work" (second).
2. **Proof strip.** Three numbers: a page load time, a Lighthouse score, and a delivery time (for example "Live in 14 days"). Mark them as sample figures.
3. **Services preview.** Three cards, from `data/services.yaml`.
4. **Featured work.** Two case study cards.
5. **How it works.** Four steps: Brief, Design, Build, Launch.
6. **Closing call to action.** One sentence and one button.

### 2. Services (`/services/`)

Goal: show what is offered and how it is delivered.

1. Intro paragraph.
2. Six service blocks: Marketing sites, Landing pages, Website redesign, Speed audits, Hosting and care plans, Design systems. Each has a title, two sentences, and three bullet points.
3. Process section: the same four steps as Home, with more detail.
4. FAQ: six questions from `data/faq.yaml`. Use the HTML `details` element (a built-in open and close box). No JavaScript.

### 3. Work (`/work/`)

Goal: show believable results.

1. A grid of four fictional case studies. Each card shows an image, client name, industry, and one result.
2. Each card opens a detail page (`/work/<name>/`) with: the problem, what was built, the result, and a small table of speed scores before and after.
3. A visible note on the page: "Sample projects. All clients are fictional."

### 4. Pricing (`/pricing/`)

Goal: help visitors pick a plan.

| Plan | Price (sample) | Includes |
| --- | --- | --- |
| Starter | $2,400 | One landing page, mobile design, contact form |
| Standard | $6,800 | Up to five pages, custom design, speed report |
| Custom | Quote | Larger sites, design systems, ongoing care |

- Show plans as three cards, with the middle one marked "Most popular."
- Below the cards, a comparison table (must scroll sideways on small screens without breaking the page).
- Below that, a short FAQ about payment and timing.

### 5. Contact (`/contact/`)

Goal: get one message from the visitor.

1. Short intro and a promise: "We reply within one business day."
2. Form fields: name, email, company (optional), project type (a select list), budget range (a select list), message.
3. A hidden spam trap field (a honeypot).
4. Success message and error message states, both readable by screen readers.
5. Side panel: a fictional email address (`hello@thewebsitefactory.com`), office hours, and a fictional city.

**Content note:** the developer writes all sample text. Keep it plain, specific, and serious. Avoid empty phrases such as "cutting-edge solutions." Use real numbers and short sentences.

## Reusable components

Build each piece once as a Hugo **partial** (a reusable template file). Style each with one Sass file.

| Component | Partial file | Notes |
| --- | --- | --- |
| Head | `partials/head.html` | Title, description, canonical link, Open Graph tags, styles link, preload for the font |
| Header | `partials/header.html` | Logo, five links, one "Start a project" button. Marks the current page with `aria-current="page"` |
| Mobile menu | inside header | Use the `details` element or a CSS-only pattern. Works without JavaScript if possible |
| Footer | `partials/footer.html` | Links, fictional address, "This is a fictional company" notice, year |
| Button | `partials/button.html` | Two styles: main (yellow) and second (outline). Takes a link and a label |
| Card | `partials/card.html` | Used for services, work, and plans |
| Section | `partials/section.html` | Wraps a heading, intro, and content with standard spacing |
| Contact form | `partials/contact-form.html` | Fields, labels, error states |
| Skip link | in `baseof.html` | "Skip to main content" as the first focusable item |

**Images**

- Use Hugo image processing to make resized copies in **WebP** (a small image format) with a fallback.
- Always set `width` and `height` so the page does not jump while loading.
- Use `loading="lazy"` on images below the first screen. Never on the main hero image.
- Case study images can be simple generated placeholders or original SVG art. Do not use stock photos of real people or real company logos.

**Icons**

- Inline SVG only. No icon font.

## Speed budget

Speed is the product. Every page must meet these limits, measured with **Lighthouse** (a free speed test built into Chrome) on a mobile profile.

| Measure | Target |
| --- | --- |
| Lighthouse Performance | 100 on every page (95 minimum) |
| Largest Contentful Paint (time until the main content shows) | under 1.5 seconds |
| Cumulative Layout Shift (how much the page jumps) | under 0.05 |
| Interaction to Next Paint (how fast it reacts to taps) | under 100 ms |
| Total page weight, Home | under 150 KB |
| CSS after compression | under 20 KB |
| JavaScript after compression | under 5 KB |
| Requests, Home | 10 or fewer |

**How to hit it**

1. Inline the small critical CSS for the first screen, or keep one small CSS file.
2. Self-host one variable font. Preload it. Subset it to Latin characters.
3. Use no third-party requests at all (no Google Fonts, no analytics, no chat widgets).
4. Serve WebP images at the right sizes with `srcset`.
5. Turn on Brotli compression and long cache times for fingerprinted files at the host.
6. Run the HTML through Hugo's minifier.

**Honest limit:** these targets are realistic for a static site like this. A 100 score can drop with a slow host or a large hero image. Test on the real host before sign-off.

## Accessibility

The site must meet **WCAG 2.2 level AA** (the common international standard for accessible websites). This matters for real users and for a company that sells quality.

1. Text contrast at least 4.5 to 1. Large text and buttons at least 3 to 1. Check the yellow accent in both light and dark mode.
2. Every interactive item works with the keyboard alone. Tab order follows the visual order.
3. A visible focus ring on every link, button, and field. Minimum 3 pixels, high contrast.
4. Skip link as the first focusable item.
5. Use real landmarks: `header`, `nav`, `main`, `footer`.
6. One `h1` per page. Headings never skip levels.
7. Every form field has a visible `label`. Errors are written in text, not shown by color alone, and are linked to the field with `aria-describedby`.
8. Every meaningful image has useful `alt` text. Decorative images use `alt=""`.
9. Respect `prefers-reduced-motion`. No animation is required to understand anything.
10. Tap targets at least 44 by 44 pixels.
11. Text can be enlarged to 200 percent with no loss of content or sideways scrolling.
12. Set `lang="en"` on the `html` element.

**Testing:** run axe DevTools or Lighthouse Accessibility on every page (score 100), and do one manual pass with keyboard only and one with a screen reader (VoiceOver or NVDA).

## SEO and metadata

Even a fictional site should be built the way a real one would be.

| Page | Title (under 60 characters) | Description (under 155 characters) |
| --- | --- | --- |
| Home | TheWebsiteFactory — Fast Web Design | Fast, accessible websites for small businesses. Live in weeks, not months. |
| Services | Web Design Services — TheWebsiteFactory | Marketing sites, landing pages, redesigns, and speed audits. |
| Work | Our Work — TheWebsiteFactory | Four sample projects with before and after speed scores. |
| Pricing | Pricing — TheWebsiteFactory | Three clear plans. No hidden fees. |
| Contact | Contact — TheWebsiteFactory | Tell us about your project. We reply in one business day. |

**Required in every page head**

- Unique `title` and `meta description` (from front matter, with a default).
- Canonical link.
- Open Graph and Twitter card tags, with one generated social image.
- `robots.txt` and an auto-made `sitemap.xml` (Hugo builds it).
- Favicon as SVG, plus a 180 pixel touch icon.
- JSON-LD structured data (machine-readable facts) for `Organization` on Home and `FAQPage` on Services.

**Important:** this is a fictional site. Add `<meta name="robots" content="noindex">` on every page so search engines do not list it as a real business. Remove it only if the owner decides otherwise.

## Contact form, hosting, and deployment

A static site has no server, so the form needs a helper service.

**Contact form**

- Use a form service that accepts a plain HTML `POST`, such as Formspree, Netlify Forms, or Web3Forms. The choice depends on the host (see Open decisions).
- The form must work **without JavaScript**. Add a small script only to show an in-page success message, and only if it stays within the 5 KB limit.
- Include the spam trap field. Optionally add a simple, privacy-friendly check.
- Do not store or send visitor data to any other service.

**Hosting**

Any static host works. Recommended: Cloudflare Pages or Netlify.

- Free tier is enough.
- Automatic build from Git on every push.
- Set the Hugo version as an environment variable to match `.hugo-version`.
- HTTPS on. Redirect `www` to the main domain, or the reverse.
- Add headers: long cache for fingerprinted files, short cache for HTML, plus `Content-Security-Policy`, `X-Content-Type-Options`, and `Referrer-Policy`.

**Domain**

TheWebsiteFactory.com is a fictional name. The developer must not register it or point it at a live site unless the owner says so. Use the host's preview address during development.

**README must include**

1. How to install Hugo Extended.
2. How to run the local server.
3. How to build.
4. How to edit services, plans, and FAQ in `data/`.
5. How to add a case study.
6. How to change colors and fonts in the Sass variables.

## Acceptance checklist and open decisions

The project is done when every box below is checked.

**Acceptance checklist**

- [ ] Five pages exist and match the page specs above.
- [ ] `hugo --minify --gc` builds with zero warnings.
- [ ] All styles are written in Sass and follow the folder layout.
- [ ] Colors, type, and spacing come from Sass variables only.
- [ ] Lighthouse scores meet the speed budget on all five pages (mobile).
- [ ] Home page is under 150 KB and 10 requests.
- [ ] Accessibility passes: axe shows no issues, keyboard pass done, screen reader pass done.
- [ ] Layout works at 320, 600, 900, and 1200 pixels wide.
- [ ] Light and dark modes both look right and pass contrast.
- [ ] Contact form sends a test message on the live host.
- [ ] Every page has a unique title, description, and canonical link.
- [ ] `noindex` is set, and the fictional notice shows in the footer and on Work.
- [ ] No third-party scripts, fonts, or trackers.
- [ ] README is complete and a new developer can build the site from it in 10 minutes.
- [ ] Code is in Git with clear commits.

**Open decisions for the owner**

| Decision | Default in this brief | Other choices |
| --- | --- | --- |
| Visual look | Clean modern with yellow accent | Bold factory, retro-future, dark and techy |
| Host | Cloudflare Pages | Netlify, GitHub Pages |
| Form service | Formspree or the host's built-in form | Web3Forms |
| Font | Inter (variable) | Any open-license variable font |
| Search listing | `noindex` (hidden) | Allow indexing |
| Blog | Not included | Add later as a sixth section |
