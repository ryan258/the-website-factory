# 101 Ways to Use The Website Factory (For Fun & Profit)

**TL;DR:** This is a list of 101 ways to earn money with this factory. Each one names a real problem, the preset and sections to use, and a way to charge. The best plays bring **repeat income** (monthly care plans), not one-off builds.

---

## How to read this guide

Each play has four short lines:

- **Need:** the problem a real business has.
- **Build:** the preset to start from and the sections to stack, written as `module/variant`.
- **Charge:** a way to price it. This guide gives pricing *models*, not amounts. You set the amounts.
- **Watch:** the one thing that can go wrong.

Plays marked ★ are the strongest earners. They solve a problem that costs the business money every month, so they are easy to sell as a monthly plan.

---

## Read this first

### What the factory has today

- **30 section types** (called modules) with **61 layouts** (called variants). Listed in `data/modules.json`.
- **8 presets** (ready-made starting plans): `agency`, `contractor`, `consultant`, `local-service`, `clinic`, `restaurant`, `nonprofit`, and `258webco`.
- **5 color palettes**, each checked for readable contrast: `studio`, `forest`, `harbor`, `terracotta`, `plum`.
- **5 font pairings**, all self-hosted and free to use: `modern`, `editorial`, `warm`, `friendly`, `readable`.
- **AI tools:** Claude can draft a page plan from a written brief. An MCP server (a way for an AI assistant to call the factory's tools) is in `.mcp.json`.
- **Safety checks:** a site cannot go public while it still says "To be confirmed" or uses the example domain.

### What you need installed

| Tool | Version | Why |
| --- | --- | --- |
| Python | 3.9 or newer | Runs the helper scripts |
| Hugo **Extended** | 0.166.0 | Builds the site. Must be the Extended build |
| Dart Sass | 1.104.1 | Builds the styles. `python3 scripts/setup.py` installs it |
| Node | 22 (optional) | Only for browser and speed checks (`npm ci`) |
| `anthropic` Python package | optional | Only for AI drafting (`pip install -r requirements-dev.txt`) |

### The loop you will run most

```sh
python3 scripts/factory.py      # check the settings (fast, no build)
python3 scripts/build.py        # check, build, check the output, then publish to public/
python3 scripts/check_site.py   # check the output again
python3 scripts/build.py --serve --port 1313
# http://127.0.0.1:1313/   the selected site
```

`--serve` does not reload by itself. Rebuild after each edit.

For the internal workshop (planner, section catalog, and style guide):

```sh
python3 scripts/build.py --workshop --serve --port 1314
# http://127.0.0.1:1314/site-kit/            client planner
# http://127.0.0.1:1314/site-kit/catalog/    every section and layout
# http://127.0.0.1:1314/site-kit/style-guide/
```

### Start a client copy

The easy way asks one question at a time, with lettered choices:

```sh
python3 scripts/new_site.py --guided
```

Or all at once:

```sh
python3 scripts/new_site.py ../client-name --name "Client Name" --preset clinic --palette harbor --fonts readable
```

A new copy starts safe. Search engines are blocked. The form is off. The domain is a fake example. Sample text stays marked as sample until you replace it.

### From a brief to a checked draft in one command

```sh
python3 scripts/factory_run.py brief.md ../client-name   # uses the Claude API (this costs money)
python3 scripts/factory_run.py --plan plan.json ../client-name   # free: uses a planner export
```

The AI is told to use only facts from the brief. Anything missing becomes "To be confirmed". The copy gets a `docs/plan-review.md` list of what a person must confirm.

### How a page is put together

```
data/factory.json          → which preset is selected
  └─ data/presets/<preset>.json
       ├─ pages.<key>.sections[]   the page order: [{ module, variant, content }, …]
       └─ sections.<key>           the words each section shows
data/modules.json          → what each module allows
data/site.yaml             → name, contact details, navigation, colors, fonts
content/<page>/_index.md   → the browser title and search description
```

To add a section, add one entry to the page's `sections` list and one block under `sections`. To remove a section, delete its entry. Copy a correct starting block from `data/examples.json` in the master (client copies do not include that file).

### The 30 modules

| Module | Layouts | Must have | Each item also needs |
| --- | --- | --- | --- |
| `hero` | `split`, `centered`, `compact` | title, intro, action | — |
| `services` | `cards`, `rows` | title, items | — |
| `work` | `gallery`, `editorial` | title, items | needs a `work` page |
| `process` | `steps`, `rows` | title, items | — |
| `about` | `split`, `editorial` | title, intro, body | — |
| `team` | `cards`, `rows` | title, items | — |
| `faq` | `accordion`, `open` | title, items | — |
| `pricing` | `cards`, `rows` | title, items, notice | — |
| `areas` | `cards`, `rows` | title, items, notice | — |
| `testimonials` | `quotes`, `featured` | title, items, notice | — |
| `stats` | `strip`, `cards` | title, items, notice | — |
| `cta` | `band`, `quiet` | title, intro, action | — |
| `contact` | `panel`, `compact` | title, intro, items, notice | — |
| `resources` | `cards`, `rows` | title, items | — |
| `comparison` | `table`, `cards` | title, items, notice | `scope`, `best` |
| `before-after` | `panels`, `stacked` | title, items, notice | — |
| `features` | `grid`, `split` | title, items | — |
| `logos` | `grid`, `inline` | title, items, notice | — |
| `timeline` | `vertical`, `cards` | title, items | — |
| `bento` | `mosaic`, `compact` | title, items | — |
| `fit` | `split`, `stacked` | title, intro, items, notice | `group`: `fit` or `alternative` |
| `inclusions` | `columns`, `stacked` | title, intro, items, notice | `group`: `included` or `excluded` |
| `preparation` | `checklist`, `ordered` | title, intro, items, notice | — |
| `hours` | `table`, `list` | title, intro, items, notice | — |
| `visit` | `details`, `cards` | title, intro, items, notice | — |
| `menu` | `table`, `cards` | title, intro, items, notice | `value` (price or scope) |
| `events` | `agenda`, `cards` | title, intro, items, notice | `when`, `place` |
| `policies` | `accordion`, `open` | title, intro, items, notice | — |
| `glossary` | `definitions`, `disclosures` | title, intro, items, notice | — |
| `support` | `routes`, `steps` | title, intro, items, notice | `url`, `link_label` |

Every item needs a `title` and `text`. Only the `work` module shows item images.

### The 8 presets

| Preset | Pages | Home page stack |
| --- | --- | --- |
| `agency` | home, services, work, pricing, contact | `hero/split` → `stats/strip` → `services/cards` → `work/gallery` → `process/steps` → `cta/band` |
| `contractor` | home, services, about, contact | `hero/split` → `services/cards` → `about/editorial` → `process/steps` → `areas/cards` → `cta/band` |
| `consultant` | home, services, about, contact | `hero/centered` → `services/cards` → `about/editorial` → `process/steps` → `resources/cards` → `cta/band` |
| `local-service` | home, services, about, contact | `hero/split` → `services/cards` → `about/editorial` → `process/steps` → `areas/cards` → `cta/band` |
| `clinic` | home, services, about, contact | `hero/split` → `services/cards` → `preparation/checklist` → `hours/table` → `cta/band` |
| `restaurant` | home, services, about, contact | `hero/split` → `services/cards` → `menu/cards` → `hours/table` → `cta/band` |
| `nonprofit` | home, services, about, contact | `hero/split` → `services/cards` → `support/routes` → `timeline/vertical` → `cta/band` |
| `258webco` | home, services, contact, privacy | `hero/split` → `stats/strip` → `services/cards` → `process/steps` → `cta/band` |

### Rules the checks enforce

`scripts/factory.py` stops the build when a rule is broken:

1. Each page starts with **one** `hero`, and only one.
2. Every preset has a `home` page and a `contact` page.
3. Some page must have a `services` section. The contact form uses its items as the "project type" choices.
4. The `work` module needs a page called `work`.
5. The "must have" fields in the table above are filled in.
6. Links in sections can be:
   - a page in the preset: `/services/`
   - a spot on a page: `/services/#questions` (that page needs a section with `"anchor": "questions"`)
   - email: `mailto:hello@example.com`
   - phone: `tel:+1 312 555 0100` (7 to 15 digits)
7. Links to other websites are **not** allowed in sections. Put them in a Markdown page body instead.
8. Images must be real files under `assets/`.
9. The business name in `data/site.yaml` must match the preset's name.
10. Each font needs its license file beside it.

`scripts/check_site.py` checks the built pages:

- Page titles under 60 characters. Search descriptions under 155. No repeats.
- One main heading (`<h1>`) per page. Every internal link works.
- CSS under 20 KB and JavaScript under 5 KB each, compressed. Fonts preloaded under 90 KB.
- No scripts, styles, fonts, or images from other websites.
- A public build fails if any page still says "To be confirmed" or uses the example domain.

`python3 scripts/claims.py` lists prices, percentages, counts, ratings, testimonials, and words like "best" or "guaranteed". The business must confirm each one. Only then does it go in the preset's `approved_claims` list.

### Going live: the switches that start off

A new copy cannot go public by accident. To launch, you change these on purpose:

1. **Search engines:** build with `HUGO_PARAMS_NOINDEX=false`.
2. **Domain:** build with `--base-url https://their-domain.com/`.
3. **Contact form:** on Cloudflare Pages, the form stores messages in KV (Cloudflare's simple storage). Turn it on with the deploy workflow's **Accept enquiries** box. On other hosts, set `params.formAction` to an outside form service (for example Formspree). See `docs/cloudflare-setup.md`.
4. **Sample text:** replace every sample name, price, and result. A new business name does not approve the rest of the words.
5. **Contact details:** `data/site.yaml` starts with `hello@example.invalid`.

Then run `python3 scripts/handover.py --build` for a plain-language handover report.

### Honest claims

What the factory has measured: clean builds, the checks above, and automated accessibility checks (axe, WCAG A/AA) on every layout in light and dark mode. See `docs/acceptance.md`.

What you must measure yourself, per client: speed scores (Lighthouse), hosted speed, screen-reader and real-phone testing, and live form delivery. If a play sells a number, measure it on the finished site first:

```sh
npm run check:browser
python3 -m http.server 14722 --bind 127.0.0.1 --directory public
npm run audit -- http://127.0.0.1:14722/
```

---

## Table of contents

1. [Monthly income plays (#1–#15)](#1-monthly-income-plays)
2. [Local businesses with urgent needs (#16–#40)](#2-local-businesses-with-urgent-needs)
3. [Health, legal, and money services (#41–#50)](#3-health-legal-and-money-services)
4. [Rescue and fix-it services (#51–#62)](#4-rescue-and-fix-it-services)
5. [AI-assisted production (#63–#74)](#5-ai-assisted-production)
6. [Sales and closing tools (#75–#83)](#6-sales-and-closing-tools)
7. [Partners and referral channels (#84–#91)](#7-partners-and-referral-channels)
8. [Products you can sell (#92–#96)](#8-products-you-can-sell)
9. [Community projects and fun builds (#97–#101)](#9-community-projects-and-fun-builds)
10. [Appendix: the edits behind all 101](#appendix-the-edits-behind-all-101)

---

## 1. Monthly income plays

These turn one build into steady monthly income. Start here.

**1. ★ The website care plan**
- **Need:** Owners want their site kept correct, but they do not want to learn how.
- **Build:** Any client copy. Each month, change the words they send, then run `factory.py` → `build.py` → `check_site.py` → `handover.py --build`.
- **Charge:** A flat monthly fee with a set number of edits. Extra edits are billed separately.
- **Watch:** Write the edit limit in the agreement. Without it, the plan turns into unpaid work.

**2. ★ Seasonal hours and closures service**
- **Need:** Wrong holiday hours send customers to a locked door. That costs sales and trust.
- **Build:** `hours/table` on Home and `hours/list` on Contact (the `clinic` and `restaurant` presets have both). Put exceptions in the section's `notice`.
- **Charge:** Part of the care plan, or a small yearly "holiday hours" package.
- **Watch:** Confirm the time zone and every date with the owner in writing.

**3. ★ Menu and price-list updates**
- **Need:** Restaurants and salons change prices often. An old menu online causes arguments at the counter.
- **Build:** `menu/table` or `menu/cards`. Each item needs a `value`. Start from `--preset restaurant`.
- **Charge:** Monthly plan with a set number of menu changes.
- **Watch:** Every price is a claim. Add it to `approved_claims` only after the owner confirms it.

**4. ★ Events calendar upkeep**
- **Need:** Venues, churches, and clubs lose visitors when the events list is out of date.
- **Build:** `events/agenda` (each item needs `when` and `place`). The `restaurant` preset already has one on Services.
- **Charge:** Monthly plan. Include removing past events.
- **Watch:** An old event left online looks like the business is closed. Remove expired items each month.

**5. ★ Policy page upkeep**
- **Need:** Booking, cancellation, and refund rules change. Old rules online lead to disputes.
- **Build:** `policies/accordion` for long lists, `policies/open` for short ones.
- **Charge:** Care-plan add-on, billed per change.
- **Watch:** Use the owner's exact approved wording. Do not write legal terms yourself.

**6. Quarterly content refresh**
- **Need:** Sites go stale. Old offers and old staff names make a business look careless.
- **Build:** Walk every page with the owner. Update `services`, `team`, `faq`, and `pricing` sections.
- **Charge:** A fixed fee every three months.
- **Watch:** Run `python3 scripts/claims.py` after each refresh. New copy often adds new claims.

**7. New-service launch pages**
- **Need:** A business adds a service and needs a page for it fast.
- **Build:** Add a page key plus `content/<page>/_index.md`. Stack `hero/compact` → `fit/split` → `inclusions/columns` → `faq/accordion` → `cta/band`.
- **Charge:** A fixed fee per launch page.
- **Watch:** Add the new service to the `services` section too, so it shows in the contact form.

**8. Monthly enquiry report**
- **Need:** Owners do not know how many people contacted them, or about what.
- **Build:** On Cloudflare, run `python3 scripts/enquiries.py export --format csv -o enquiries.csv` and summarize it for them.
- **Charge:** Monthly add-on.
- **Watch:** The export holds personal data. Send it safely, and delete your copy after.

**9. Staff and team page upkeep**
- **Need:** Staff come and go. A departed person listed online confuses customers.
- **Build:** `team/cards` or `team/rows`.
- **Charge:** Part of the care plan.
- **Watch:** Get each person's consent before listing their name.

**10. FAQ growth plan**
- **Need:** Staff answer the same questions by phone every day. That costs time.
- **Build:** Ask staff for the top questions each month. Add them to `faq/accordion`. Link to them with anchors, for example `/services/#questions`.
- **Charge:** Monthly plan with a set number of new answers.
- **Watch:** The owner must approve each answer.

**11. Hosting and launch management**
- **Need:** Owners do not want to deal with domains, hosting, and deploys.
- **Build:** Cloudflare Pages setup from `docs/cloudflare-setup.md`. Releases run from the manual GitHub workflow.
- **Charge:** Monthly or yearly fee.
- **Watch:** The client should own the domain and the Cloudflare account. You get access, not ownership.

**12. Contact form monitoring**
- **Need:** A broken form quietly loses customers.
- **Build:** Set a `NOTIFICATION_WEBHOOK` secret for alerts. Send a test enquiry each month and confirm it was stored.
- **Charge:** Care-plan add-on.
- **Watch:** Without a webhook, nobody is alerted. Someone must check the stored messages on a schedule.

**13. Yearly accessibility re-check**
- **Need:** Content changes can break accessibility. Many buyers now require an accessibility statement from vendors.
- **Build:** Run `npm run check:browser` after each content change. Write a short yearly report.
- **Charge:** A yearly fee.
- **Watch:** Automated checks do not prove full WCAG conformance. Sell a manual review as a separate item.

**14. Handover-report subscription**
- **Need:** Owners want proof the site is healthy.
- **Build:** `python3 scripts/handover.py --build --output docs/acceptance.md` each month.
- **Charge:** Part of the care plan.
- **Watch:** The report lists what it cannot check. Do not remove that list.

**15. Multi-location upkeep**
- **Need:** A business with several branches needs each branch's hours and directions correct.
- **Build:** One page per branch. Each gets `visit/details` + `hours/table`. Link to them from `areas/cards` on Home.
- **Charge:** Monthly fee per location.
- **Watch:** Check page titles stay under 60 characters. Long branch names hit this limit first.

---

## 2. Local businesses with urgent needs

These businesses lose money every day their site is wrong or missing.

**16. ★ Emergency plumber, electrician, or locksmith**
- **Need:** People in a crisis search on a phone and call the first clear number.
- **Build:** `--preset local-service`. Home: `hero/split` → `services/cards` → `areas/cards` → `faq/open` → `contact/compact`. Put a `tel:` link in a `contact` item so the number is tappable.
- **Charge:** Fixed-fee build plus care plan.
- **Watch:** Do not claim a response time unless the owner confirms it.

**17. ★ Restaurant or cafe**
- **Need:** Customers want the menu, hours, and directions in five seconds.
- **Build:** `--preset restaurant`. It ships `menu/cards`, `hours/table`, `visit/cards`, and `events/agenda`.
- **Charge:** Build fee plus monthly menu updates (#3).
- **Watch:** Allergy information must be confirmed by the owner. Keep it in text, never only in a photo.

**18. ★ Roofer or general contractor**
- **Need:** Homeowners compare several quotes. A clear process wins trust.
- **Build:** `--preset contractor`. Add `inclusions/columns` (what the quote covers) and `before-after/panels` to Services.
- **Charge:** Build fee plus care plan.
- **Watch:** License and insurance words ("licensed", "insured") are claims. Confirm them first.

**19. HVAC and heating repair**
- **Need:** Customers need to know if they can get help today and what to prepare.
- **Build:** `--preset local-service`. Add `preparation/checklist` (model number, photos of the unit) and `comparison/table` (repair or replace).
- **Charge:** Build fee plus seasonal updates.
- **Watch:** Rebate details change. Put them in a `notice` and date them.

**20. Auto repair shop**
- **Need:** Drivers want hours, drop-off steps, and what happens next.
- **Build:** `--preset local-service`. Home: `hero/split` → `services/cards` → `hours/table` → `process/steps` → `visit/details`.
- **Charge:** Build fee plus care plan.
- **Watch:** Do not publish prices unless the shop commits to them.

**21. Hair salon or barber**
- **Need:** Clients want prices, hours, and how to book.
- **Build:** `--preset restaurant` fits well: `menu/table` for services and prices, `hours/table`, `policies/open` for late and no-show rules.
- **Charge:** Build fee plus price-list upkeep.
- **Watch:** Bookings are a contact path, not a live calendar. Say so clearly.

**22. Dog groomer or pet sitter**
- **Need:** Owners want to know what their pet needs before the first visit.
- **Build:** `--preset local-service`. Add `preparation/checklist` (vaccine records) and `policies/accordion`.
- **Charge:** Build fee plus care plan.
- **Watch:** Vaccine rules must come from the business, not from you.

**23. Cleaning company**
- **Need:** Customers want to know exactly what is and is not included.
- **Build:** `--preset local-service`. Add `inclusions/columns` and `areas/cards`.
- **Charge:** Build fee plus care plan.
- **Watch:** The `inclusions` notice should say the signed quote comes first.

**24. Moving company**
- **Need:** People are stressed and want a clear plan.
- **Build:** `--preset contractor`. Add `timeline/vertical` (moving-day steps) and `preparation/checklist` (what to pack first).
- **Charge:** Build fee plus seasonal updates.
- **Watch:** Damage and insurance terms belong in `policies`, in the owner's words.

**25. Landscaper and lawn care**
- **Need:** Customers want to know the service area and the season plan.
- **Build:** `--preset contractor`. Add `events/cards` for seasonal visits and `areas/rows`.
- **Charge:** Build fee plus seasonal updates.
- **Watch:** Keep the service area exact. A vague area brings calls you cannot serve.

**26. Fitness studio or gym**
- **Need:** New members want the class schedule and first-visit steps.
- **Build:** `--preset local-service`. Add `events/agenda` for classes, `preparation/ordered` for the first visit, and `pricing/cards`.
- **Charge:** Build fee plus monthly schedule updates.
- **Watch:** Membership prices are claims. Confirm them.

**27. Daycare or after-school program**
- **Need:** Parents need hours, rules, and what to pack.
- **Build:** `--preset clinic` shape works: `preparation/checklist`, `hours/table`, `policies/accordion`, `visit/details`.
- **Charge:** Build fee plus yearly policy updates.
- **Watch:** Licensing claims must be confirmed. Never show children's photos without written consent.

**28. Tutor or music teacher**
- **Need:** Parents want to know if the teacher fits their child.
- **Build:** `--preset consultant`. Add `fit/split` (good fit and better alternatives) and `pricing/rows`.
- **Charge:** Small fixed-fee build.
- **Watch:** Results like "grades went up" are claims. Leave them out unless proven.

**29. Driving school**
- **Need:** Students need the steps from first lesson to test day.
- **Build:** `--preset consultant`. Add `timeline/vertical` and `preparation/checklist` (ID and permit).
- **Charge:** Build fee plus care plan.
- **Watch:** Test rules differ by place. Confirm them with the owner.

**30. Wedding and event venue**
- **Need:** Couples want spaces, packages, and dates.
- **Build:** `--preset restaurant`. Use `bento/mosaic` for spaces, `pricing/cards` for packages, `visit/cards`, and `policies/accordion`.
- **Charge:** Build fee plus event-season updates.
- **Watch:** Availability is not live. Tell couples to ask.

**31. Caterer or private chef**
- **Need:** Clients want sample menus and what a booking includes.
- **Build:** `--preset restaurant`. Use `menu/cards`, `inclusions/stacked`, and `faq/accordion` for dietary questions.
- **Charge:** Build fee plus menu upkeep.
- **Watch:** Per-person prices are claims. Confirm them.

**32. Food truck**
- **Need:** Fans need to know where the truck is this week.
- **Build:** `--preset restaurant`. Put the weekly stops in `events/agenda` (each needs `when` and `place`).
- **Charge:** Weekly or monthly update plan.
- **Watch:** Old stops send people to an empty lot. Update every week.

**33. Bakery with pre-orders**
- **Need:** Customers want to know what to order and how far ahead.
- **Build:** `--preset restaurant`. Add `preparation/ordered` (order steps) and `policies/open` (deposits).
- **Charge:** Build fee plus seasonal menu updates.
- **Watch:** There is a sample bakery brief in `evals/briefs/bakery.md` to practice with.

**34. Farm stand or farmers' market vendor**
- **Need:** Shoppers want what is in season and when the stand is open.
- **Build:** `--preset restaurant`. Use `menu/table` for produce, `hours/table`, and `visit/details`.
- **Charge:** Seasonal update plan.
- **Watch:** Update the menu when crops change.

**35. Self-storage or equipment rental**
- **Need:** Renters want sizes, rules, and access hours.
- **Build:** `--preset local-service`. Use `comparison/table` for unit sizes, `hours/list`, and `policies/accordion`.
- **Charge:** Build fee plus care plan.
- **Watch:** Rental prices change. Keep them in one `menu` or `pricing` section.

**36. Property manager**
- **Need:** Tenants need repair routes and emergency numbers.
- **Build:** `--preset local-service`. Add `support/routes` (each item needs `url` and `link_label`) and `glossary/definitions`.
- **Charge:** Build fee plus care plan.
- **Watch:** Support routes must be real. Do not suggest 24-hour help unless it exists.

**37. Home inspector**
- **Need:** Buyers do not understand inspection words.
- **Build:** `--preset consultant`. Add `glossary/disclosures`, `preparation/checklist`, and `inclusions/columns`.
- **Charge:** Build fee plus care plan.
- **Watch:** Certifications are claims. Confirm them.

**38. Photographer**
- **Need:** Clients want to see the work and the packages.
- **Build:** `--preset agency` (it has the `work` page for galleries). Add `pricing/cards` and `faq/accordion`.
- **Charge:** Build fee plus gallery updates.
- **Watch:** The `work` image text currently reads "fictional project design". Edit `layouts/partials/factory/module.html` before using real photos.

**39. Tour guide or local experience**
- **Need:** Visitors want dates, meeting points, and what to bring.
- **Build:** `--preset restaurant`. Use `events/cards`, `visit/details`, and `preparation/checklist`.
- **Charge:** Build fee plus seasonal updates.
- **Watch:** Access information must be specific. "Accessible" alone is not enough.

**40. Local shop with click-and-collect**
- **Need:** Customers want to order ahead and pick up.
- **Build:** `--preset local-service`. Add `preparation/ordered` (order steps), `hours/table`, and `visit/details`.
- **Charge:** Build fee plus care plan.
- **Watch:** The site does not take payments. Link to their own shop system from a Markdown page.

---

## 3. Health, legal, and money services

These pay well because trust matters so much. They also carry more rules. **The client must approve every claim.**

**41. ★ Dental or medical clinic**
- **Need:** Patients need hours, what to bring, and how to get there.
- **Build:** `--preset clinic`. It ships `preparation/checklist`, `hours/table`, `visit/details`, and `hours/list`.
- **Charge:** Higher build fee plus care plan.
- **Watch:** Do not collect health details through the contact form. Keep it for general questions only.

**42. Physical therapist or chiropractor**
- **Need:** New patients want to know what the first visit is like.
- **Build:** `--preset clinic`. Add `timeline/vertical` (first visit) and `fit/split`.
- **Charge:** Build fee plus care plan.
- **Watch:** Health outcome claims need proof. `claims.py` flags words like "proven".

**43. Therapist or counselor**
- **Need:** People want to know if this therapist is right for them, without pressure.
- **Build:** `--preset clinic`. Use `fit/stacked`, `policies/accordion` (fees and cancellations), and `support/routes` for urgent help.
- **Charge:** Build fee plus care plan.
- **Watch:** Crisis numbers must be current and correct. Check them every quarter.

**44. Veterinary clinic**
- **Need:** Pet owners need emergency hours and what to bring.
- **Build:** `--preset clinic`. Put emergency information in the hero `note` and in `support/routes`.
- **Charge:** Build fee plus care plan.
- **Watch:** Emergency information works without JavaScript here. Keep it that way; do not add embeds.

**45. Pharmacy or optician**
- **Need:** Customers want hours, services, and refill steps.
- **Build:** `--preset clinic`. Use `hours/table`, `services/rows`, and `preparation/ordered`.
- **Charge:** Build fee plus hours upkeep (#2).
- **Watch:** Insurance lists change often. Date them in the `notice`.

**46. Small law firm**
- **Need:** Clients want the practice areas and what to bring to a first meeting.
- **Build:** `--preset consultant`. Use `features/split` (practice areas), `preparation/checklist`, `glossary/definitions`, and `policies/accordion`.
- **Charge:** Higher build fee plus care plan.
- **Watch:** Bar rules limit advertising. The lawyer must approve every sentence.

**47. Accountant or tax preparer**
- **Need:** Clients need deadlines and a document checklist.
- **Build:** `--preset consultant`. Use `preparation/checklist`, `events/agenda` (deadlines), and `fit/split`.
- **Charge:** Build fee plus a yearly tax-season update.
- **Watch:** Deadlines change each year. Put a date in each `notice`.

**48. Financial planner**
- **Need:** Clients want to understand fees and how advice works.
- **Build:** `--preset consultant`. Use `inclusions/columns`, `pricing/rows`, `glossary/disclosures`, and `process/steps`.
- **Charge:** Higher build fee plus care plan.
- **Watch:** Fee and performance claims are regulated. The planner signs off on all copy.

**49. Insurance agent**
- **Need:** Clients want to know which policy fits.
- **Build:** `--preset consultant`. Use `comparison/table` and `fit/split`.
- **Charge:** Build fee plus care plan.
- **Watch:** Do not name insurers or prices unless the agent confirms them.

**50. Immigration or visa consultant**
- **Need:** Clients need clear steps and document lists.
- **Build:** `--preset consultant`. Use `timeline/vertical`, `preparation/checklist`, and `glossary/definitions`.
- **Charge:** Build fee plus rule-change updates.
- **Watch:** Rules change often. Date every notice. Do not give legal advice in the copy.

---

## 4. Rescue and fix-it services

These start with a problem the owner already feels. That makes them easy to sell.

**51. ★ Slow-website rescue**
- **Need:** A slow site loses visitors, especially on phones.
- **Build:** Rebuild the pages in a client copy. Measure the old site and the new build with `npm run audit` on the same day.
- **Charge:** Fixed fee, with the before-and-after report included.
- **Watch:** Only promise numbers you measured on the finished site.

**52. ★ WordPress exit**
- **Need:** Plugin updates, security scares, and hosting bills wear owners down.
- **Build:** Map each old page to a preset page and a section stack. Long articles become Markdown pages.
- **Charge:** Fixed fee per page, plus a care plan.
- **Watch:** Keep old addresses working, or list redirects for the host. Lost addresses lose search traffic.

**53. ★ Hacked-site rebuild**
- **Need:** The site was hacked and the owner wants it gone and safe.
- **Build:** Fresh client copy. The output is static files: no database and no admin login to break into.
- **Charge:** Rush fee plus care plan.
- **Watch:** The contact form is the only live part. Keep it off until you set it up properly.

**54. Accessibility fix-up**
- **Need:** Owners fear complaints and want a site everyone can use.
- **Build:** Rebuild on the factory. Run `npm run check:browser` in light and dark mode at 320 to 1200 pixels.
- **Charge:** Fixed fee plus the yearly re-check (#13).
- **Watch:** Automated checks are not full WCAG conformance. Offer a manual review as a separate item.

**55. Wix or Squarespace exit**
- **Need:** Monthly builder fees and limits frustrate the owner.
- **Build:** Match their look with variants and a palette. Pick fonts with `--fonts`.
- **Charge:** Fixed fee.
- **Watch:** Tell them what they lose (the drag-and-drop editor) and what they gain.

**56. Privacy clean-up**
- **Need:** Trackers and outside fonts send visitor data to other companies.
- **Build:** The factory loads nothing from other websites. Fonts are self-hosted. The `258webco` preset shows a privacy page built with `policies/open`.
- **Charge:** Fixed fee.
- **Watch:** Adding outside tools later breaks this. The output check will fail on them.

**57. Wrong-information audit**
- **Need:** Old hours, prices, and staff names on a site cost trust.
- **Build:** Run `python3 scripts/claims.py` on the rebuilt site. Walk the list with the owner.
- **Charge:** Fixed-fee audit, then a care plan.
- **Watch:** The tool finds claims. It cannot tell if they are true. The owner decides.

**58. Mobile-first rebuild**
- **Need:** Most local visitors use phones, and the old site is hard to use on one.
- **Build:** Every layout is checked at 320 pixels wide. Keep Home to five sections so the call to action is close.
- **Charge:** Fixed fee.
- **Watch:** Test on a real phone too. The automated check is not a real device.

**59. Single-page site upgrade**
- **Need:** A business has one long page that is hard to scan.
- **Build:** Split it into Home, Services, About, and Contact. Use anchors for deep links, such as `/services/#questions`.
- **Charge:** Fixed fee.
- **Watch:** Each page needs its own unique title and description.

**60. Broken-contact-form fix**
- **Need:** The old form sends messages nowhere.
- **Build:** Cloudflare Pages form with KV storage, or an outside service through `params.formAction`.
- **Charge:** Fixed fee plus monitoring (#12).
- **Watch:** Send a real test message. Confirm it arrived before calling it fixed.

**61. Low-data rebuild for rural customers**
- **Need:** Customers on slow connections give up on heavy sites.
- **Build:** Keep images few. Use `bento/compact` rather than large galleries.
- **Charge:** Fixed fee.
- **Watch:** Test with a slow network setting in the browser before promising speed.

**62. Rebrand refresh**
- **Need:** A new logo and colors, but the old site looks different.
- **Build:** Update `theme.*` in `data/site.yaml`, swap fonts, then run `python3 scripts/contrast.py` and `npm run check:browser`.
- **Charge:** Fixed fee.
- **Watch:** A valid color code does not mean readable text. Always re-check contrast.

---

## 5. AI-assisted production

These use the AI tools to work faster. The human still checks every fact.

**63. ★ Brief-to-draft in one day**
- **Need:** Clients want to see something fast.
- **Build:** `python3 scripts/factory_run.py brief.md ../client`. It drafts, compiles, copies, builds, and checks.
- **Charge:** A paid "first draft" step that counts toward the full build.
- **Watch:** Each run uses the paid Claude API. Every gap stays "To be confirmed".

**64. Paid discovery with the planner**
- **Need:** Clients want to shape the site before paying for all of it.
- **Build:** Use the planner at `/site-kit/`. Export the plan, then `python3 scripts/from_plan.py plan.json --name client --write`.
- **Charge:** Fixed discovery fee.
- **Watch:** The plan is a planning file, not a finished site.

**65. Agent-run factory**
- **Need:** You want an AI assistant to do routine work safely.
- **Build:** The MCP server in `.mcp.json` gives tools like `validate_preset`, `check_claims`, `compile_plan`, and `create_client_site`.
- **Charge:** Your time drops. Your price stays tied to the result.
- **Watch:** None of the tools commit, deploy, or turn on a form. A person still does those.

**66. "To be confirmed" interview service**
- **Need:** Drafts have gaps. Owners hate filling in forms.
- **Build:** Take the `docs/plan-review.md` list from `factory_run.py`. Ask the owner each question in a short call.
- **Charge:** Part of the build fee.
- **Watch:** Write down who confirmed each fact and when.

**67. Claims check as a service**
- **Need:** Other agencies' sites make claims nobody can back up.
- **Build:** Rebuild the copy into a preset. Run `python3 scripts/claims.py --json`.
- **Charge:** Fixed-fee review.
- **Watch:** The tool flags patterns. It cannot judge truth.

**68. Fast multi-site rollout**
- **Need:** A franchise needs many similar sites.
- **Build:** One preset per brand. One client copy per location with `new_site.py`.
- **Charge:** Setup fee plus a per-location fee.
- **Watch:** Each location's facts need their own confirmation.

**69. Draft quality scoring**
- **Need:** You want to know if AI drafts are getting better or worse.
- **Build:** `python3 scripts/eval_plans.py` scores saved drafts for free. `--live` makes paid calls.
- **Charge:** Internal. It protects quality.
- **Watch:** Do not run `--live` just to test. It costs money.

**70. AI-assisted copy review**
- **Need:** Owners write long, unclear text.
- **Build:** The planner's AI copy control prepares a prompt. Paste in a suggestion, review it, and save it as draft.
- **Charge:** Part of the build.
- **Watch:** The planner does not call a model itself. You paste the answer in.

**71. Machine-readable site summary**
- **Need:** AI search tools read sites differently from people.
- **Build:** The build writes `llms.txt`, a plain-text summary of the site for AI tools.
- **Charge:** Mention it as part of the build.
- **Watch:** It only repeats what the site says. Keep the site correct.

**72. Handover packs**
- **Need:** Clients want proof of what they got.
- **Build:** `python3 scripts/handover.py --build --output docs/acceptance.md`.
- **Charge:** Included in every build.
- **Watch:** Keep the "not checked" list in the report.

**73. Visual change checks**
- **Need:** A small edit can break a layout without anyone noticing.
- **Build:** `node scripts/visual_check.cjs --update` saves screenshots. `node scripts/visual_check.cjs` compares against them.
- **Charge:** Part of the care plan.
- **Watch:** Screenshots differ between machines. Compare on the same machine.

**74. Schema-guided editing**
- **Need:** Editors make typing mistakes in JSON files.
- **Build:** Point your editor at the files in `schemas/`. It warns about mistakes as you type.
- **Charge:** Internal. It saves time.
- **Watch:** After editing modules or tones, run `python3 scripts/schemas.py`.

---

## 6. Sales and closing tools

**75. ★ Live wireframe on the sales call**
- **Need:** Prospects cannot picture the site from a list.
- **Build:** Open `/site-kit/catalog/` and pick sections together. Rebuild and show the real page.
- **Charge:** Close the build during the call.
- **Watch:** Practice the rebuild once. `--serve` does not reload by itself.

**76. Shareable preview link**
- **Need:** The owner's partner wants to see the draft too.
- **Build:** Run **Actions → Preview Deployment** and choose `site`. The preview blocks search engines and keeps the form off.
- **Charge:** Part of the build.
- **Watch:** Anyone with the link can open it. Add Cloudflare Access if it must stay private.

**77. Same-day rebrand demo**
- **Need:** Prospects want to see their own brand, not a template.
- **Build:** Before the call, pick a palette and fonts, set their name, and rebuild.
- **Charge:** A free demo that leads to a paid build.
- **Watch:** Run `python3 scripts/contrast.py` first, so you show readable colors.

**78. Before-and-after pitch**
- **Need:** Owners do not see what is wrong with their current site.
- **Build:** Put their current words into a preset. Show both sites side by side, with speed reports from the same day.
- **Charge:** Leads to a rescue job (#51).
- **Watch:** Same day, same machine, same connection. Otherwise the numbers mean nothing.

**79. Scope with "included" and "not included"**
- **Need:** Scope creep eats your profit.
- **Build:** Put your own offer in `inclusions/columns` on your site. Use the same list in the proposal.
- **Charge:** Change orders are clear from day one.
- **Watch:** Say that the signed proposal comes first.

**80. Section menu pricing**
- **Need:** Clients want to know what drives the price.
- **Build:** Price by page and by section type. Sections that need a `notice` usually need more approved copy.
- **Charge:** A clear menu of prices.
- **Watch:** Keep your own prices in step with `data/contact.yaml` budget choices.

**81. Stakeholder workshop**
- **Need:** Several people disagree about the site.
- **Build:** Show the planner. Each person argues for one section on one page.
- **Charge:** Fixed workshop fee.
- **Watch:** Cap Home at about five or six sections.

**82. "You own it" guarantee**
- **Need:** Owners fear being locked in.
- **Build:** Show the files: Hugo templates, Sass, Python, JSON, YAML, and fonts with licenses.
- **Charge:** It raises trust, so it helps close.
- **Watch:** Be honest that Hugo 0.166.0 and Dart Sass 1.104.1 are needed to rebuild.

**83. Post-launch upsell review**
- **Need:** A new site often uses only a few section types.
- **Build:** Each quarter, suggest one useful unused section, like `fit`, `preparation`, or `policies`.
- **Charge:** Fixed fee per added section.
- **Watch:** Suggest only what solves a real visitor question.

---

## 7. Partners and referral channels

**84. ★ White-label builds for other agencies**
- **Need:** Design agencies have clients but no developer.
- **Build:** Map their designs onto the 61 layouts. Use their palette and fonts.
- **Charge:** Wholesale price per site. They add their margin.
- **Watch:** Agree who talks to the end client, and who owns the files.

**85. Accountant and bookkeeper referrals**
- **Need:** Accountants' clients ask them for web help.
- **Build:** Offer a fixed package for their clients, such as `local-service` plus a care plan.
- **Charge:** A referral thank-you, where local rules allow it.
- **Watch:** Some professions limit referral fees. Check first.

**86. Chamber of commerce member package**
- **Need:** Small members want a simple, affordable site.
- **Build:** One preset per business type. A fixed section list.
- **Charge:** A member price, with volume from the chamber.
- **Watch:** Keep the package fixed. Extras are change orders.

**87. Franchise location sites**
- **Need:** Head office wants brand control. Locations want local details.
- **Build:** One shared preset. Each location changes only `hours`, `visit`, `team`, and `areas`.
- **Charge:** Setup fee plus per-location monthly fee.
- **Watch:** Title length limits hit long location names first.

**88. Marketing consultant partnership**
- **Need:** Consultants write strategy but need someone to build.
- **Build:** They write the brief. You run `factory_run.py` and finish the site.
- **Charge:** A fixed build fee, billed to them or their client.
- **Watch:** The consultant's claims still need the business's confirmation.

**89. Web host or IT provider partnership**
- **Need:** IT providers get asked for websites but do not build them.
- **Build:** You build. They host or manage the domain.
- **Charge:** Build fee, with a shared care plan.
- **Watch:** Agree who fixes what when something breaks.

**90. Print and sign shop partnership**
- **Need:** Printers make menus and signs. The website shows old information.
- **Build:** When the printer updates a menu, you update `menu/table` too.
- **Charge:** A bundled "print plus web" update.
- **Watch:** One approved source of truth for prices.

**91. Nonprofit grant partner**
- **Need:** Grants often pay for websites, but charities lack a builder.
- **Build:** `--preset nonprofit`. It ships `support/routes` and `timeline/vertical`.
- **Charge:** Grant-funded fixed fee.
- **Watch:** Impact numbers ("families helped") are claims. Get proof.

---

## 8. Products you can sell

The repository has **no `LICENSE` file yet**, and `package.json` is marked private. Add the license you want before you sell anything built from this code. Each font's license (`static/fonts/OFL-*.txt`) must travel with it.

**92. Niche preset packs**
- **Need:** Other builders want a ready plan for a trade.
- **Build:** One `data/presets/<slug>.json` plus a palette and font pairing. `new_site.py` finds new presets by itself.
- **Charge:** A one-time price per pack.
- **Watch:** Test each pack in a fresh client copy. A pack that fails `factory.py` is a refund.

**93. Page-plan templates**
- **Need:** Owners want to plan before hiring.
- **Build:** Planner export files (JSON) for common businesses. Buyers import them at `/site-kit/`.
- **Charge:** Low price, or free as a lead magnet.
- **Watch:** Plans hold no real facts. Say so.

**94. Course: build client sites safely**
- **Need:** New freelancers break things and make risky claims.
- **Build:** Teach with the checks. Break something on purpose (a second hero, an outside link) and let `factory.py` explain it.
- **Charge:** Course fee.
- **Watch:** Teach the "never invent facts" rule first.

**95. Content checklists for owners**
- **Need:** Owners do not know what to gather before a build.
- **Build:** Turn the module "must have" fields into a checklist per business type.
- **Charge:** Free lead magnet, or included in discovery.
- **Watch:** Keep it short. Long lists do not get done.

**96. Starter kit for other studios**
- **Need:** Small studios want a tested production system.
- **Build:** The master, with the workshop, checks, and docs.
- **Charge:** A license fee, with optional support.
- **Watch:** Add a license first. Decide if buyers can resell it.

---

## 9. Community projects and fun builds

Good for practice, portfolio pieces, and goodwill.

**97. Food bank or mutual aid group**
- **Need:** People need to know where and when to get help.
- **Build:** `--preset nonprofit`. Add `hours/table` and `visit/details`. There is a sample brief in `evals/briefs/food-bank.md`.
- **Charge:** Free or low cost, as community work and a portfolio piece.
- **Watch:** Opening times must be exact. People travel based on them.

**98. School club or sports team**
- **Need:** Parents need schedules and what to bring.
- **Build:** `--preset nonprofit`. Use `events/agenda` and `preparation/checklist`.
- **Charge:** Small fee or free.
- **Watch:** No children's names or photos without written consent.

**99. Neighborhood association**
- **Need:** Residents need meeting dates and contact routes.
- **Build:** `--preset nonprofit`. Use `events/cards` and `support/routes`.
- **Charge:** Free or low cost.
- **Watch:** Name a person who keeps it up to date.

**100. Your own portfolio site**
- **Need:** You need a site that shows your work and process.
- **Build:** Study the `258webco` preset. It has a privacy page and no fake case studies.
- **Charge:** It wins your clients.
- **Watch:** Show only real work, with permission.

**101. Practice site from a sample brief**
- **Need:** You want to learn the whole flow without risk.
- **Build:** Export a plan from the planner, then run `python3 scripts/factory_run.py --plan plan.json ../practice` (free). Or draft from `evals/briefs/plumber.md` (this uses the paid Claude API).
- **Charge:** Nothing. It is practice.
- **Watch:** Keep it private. `noindex` and the example domain already do that.

---

## Appendix: the edits behind all 101

### 1. Add a section to a page

In `data/presets/<preset>.json`, add one entry to the page and one block of words:

```json
"pages": { "home": { "sections": [
  { "module": "hero",  "variant": "split", "content": "hero" },
  { "module": "hours", "variant": "table", "content": "opening-hours", "anchor": "hours" }
] } },
"sections": {
  "opening-hours": {
    "title": "Opening hours",
    "intro": "Walk-ins welcome during these times.",
    "notice": "To be confirmed",
    "items": [
      { "title": "Monday to Friday", "text": "To be confirmed" }
    ]
  }
}
```

Then run `python3 scripts/factory.py`. The anchor lets other sections link to `/#hours`.

### 2. Add a page

1. Make `content/<page>/_index.md` with a `title` and a `description`.
2. Add `pages.<page>` to the preset with `title`, `description`, and `sections`. The first section must be a `hero`.
3. Add the page to the navigation in `data/site.yaml` if visitors should see it there.

A content folder that is not in `pages` is left out of the build.

### 3. Add a plain Markdown page (for outside links)

```sh
cat > content/services/retainers.md <<'MD'
---
title: "Retainers"
description: "How ongoing work is scoped, reviewed, and billed."
heading: "Ongoing work, clearly scoped."
intro: "What a monthly plan covers."
---
Outside links are fine here: [an example](https://example.com/).
MD
```

### 4. Rebrand

Start a copy with `--palette` and `--fonts`, or edit `theme.*` and `font` in `data/site.yaml`. Then run `python3 scripts/contrast.py` and `npm run check:browser`.

### 5. Add a preset

Add `data/presets/<slug>.json` with a `name`, `label`, `tone` (`yellow`, `clay`, `sage`, or `blue`), `pages`, and `sections`. `new_site.py` offers it automatically.

### 6. Build under a subpath

```sh
python3 scripts/build.py --destination ../out/brand-a --base-url https://example.com/brand-a/
```

Use an empty folder. Never point it at a source folder.

### 7. The checks, in order

```sh
python3 scripts/factory.py
python3 scripts/build.py && python3 scripts/check_site.py
python3 scripts/claims.py
npm test                    # all unit and contract tests
npm run check:browser       # accessibility, layout, and security headers
python3 scripts/handover.py --build
```

Deploying, turning on search engines, and turning on the form are always a person's decision. No script here does them for you. See `docs/factory-guide.md` for editing, `docs/cloudflare-setup.md` for going live, and `roadmap.md` for what is planned.
