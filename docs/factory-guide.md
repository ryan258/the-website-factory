# Sculpt a client website

Follow [the agency delivery cycle](agency-workflow.md) in the master: agree the brief and scope before selecting components. The agency storefront is the default build. Run `python3 scripts/build.py --workshop --serve --port 1314` for internal planning at `http://127.0.0.1:1314/site-kit/`; workshop output goes to `public-workshop`.

The master includes eight business compositions (`agency`, `contractor`, `consultant`, `local-service`, `clinic`, `restaurant`, `nonprofit`, `258webco`), a project workspace at `/site-kit/`, a visual catalog at `/site-kit/catalog/`, and an interactive Living Style Guide at `/site-kit/style-guide/`. The catalog and style guide render the same components as the client sites. They are internal production surfaces. Review the selected client pages with the client.

## Start a separate copy

```sh
python3 scripts/new_site.py ../cedar-studio --name "Cedar Studio" --preset contractor
```

Choose `agency`, `contractor`, `consultant`, `local-service`, `clinic`, `restaurant`, `nonprofit`, or `258webco`. Add `--palette` with a name from `data/palettes.json` to start from a contrast-checked color set. The destination must not exist. Copies omit the workshop, unused presets, pages outside the selected composition, unrelated agency project images, generated output, dependencies, Git history, and historical acceptance evidence. Every copy starts with disabled delivery, `noindex`, an invalid example domain, and sample content.

## Compiling presets from the planning workshop

Exported project plans from `/site-kit/` can be converted directly into validated factory presets:

```sh
python3 scripts/from_plan.py path/to/plan.json --name "my-preset" --write
```

This compiles the planner JSON into `data/presets/<name>.json`, normalizes the page hierarchy (ensuring `home` first and `contact` last), injects mandatory hero headers and services, maps sections to schema contracts in `data/modules.json`, and validates the output against `scripts/factory.py` in a scratch copy, so a preview or a failed compile never changes `data/presets/`. `--write` refuses to replace an existing preset unless you add `--force`.

The compiler never invents facts. Anything the plan leaves out (prices, dates, places, service copy) is written as `To confirm with the client.`, and the command lists every section that still contains it. Replace each one with confirmed copy before client review.

- Sections may use the planner's names ("Introduction", "Services", "FAQ", …) or module keys (`hero`, `services`, `faq`). An unknown section type, or two pages that would share one address, stops the compile with an error instead of being dropped.
- The compiler never invents business facts. Any required field the plan leaves empty (prices, times, places, services) is filled with **"To be confirmed"**, and the command prints how many there are. Replace each one before publishing.
- `--write` refuses to replace an existing preset. Choose another `--name`, or add `--force` to replace it on purpose.
- The written preset can start a client copy straight away: `python3 scripts/new_site.py ../client --name "Client" --preset <name>`.

Running without `--write` previews the validated preset JSON to stdout and validates completely in-memory, leaving existing preset files on disk untouched even if the plan shares a slug.

## Edit the composition

`data/factory.json` selects the preset. Its `workshop` flag controls whether the review catalog is included by the build helper. The selected `data/presets/<preset>.json` contains:

- `name`, `label`, and `tone`: the composition identity. Tone is `yellow`, `clay`, `sage`, or `blue`.
- `pages`: page title, description, and ordered section declarations. `home` and `contact` are required.
- `sections`: the editorial content referenced by those declarations.

For example, an About section can be inserted after services:

```json
{"module": "about", "variant": "editorial", "content": "about"}
```

The first section must be the page's only `hero`. Reorder subsequent entries to change the visitor journey. Remove an entry to omit that section. Multiple instances may reference different content keys; their HTML identifiers remain unique. Remove a page from `pages` to exclude its content tree during a helper build. Remove or rewrite links to that page at the same time; validation rejects unresolved references. A direct Hugo build fails when an existing content page has no composition; use the build helper for selected-page output.

Page front matter controls browser metadata. Composition content controls the visible page sections. Update both when changing a page's purpose. `data/site.yaml` controls the real client identity, font, base light/dark palettes, contact details, and navigation labels. Preset tones style workshop previews and initialize the client's accent color when scaffolding. Edit `theme.accent` in the client copy for its final brand color.

`data/modules.json` documents each module's variants, required fields, and page dependencies. The work module requires the work page. Image references must resolve to local assets. Module links (`url` fields) accept three kinds of address, and validation checks each one:

- **A local page:** `/services/`. The page must be in the preset.
- **A spot on a page:** `/services/#questions`. A section on that page must declare the anchor, like this: `{"module": "faq", "variant": "accordion", "content": "faq", "anchor": "questions"}`. Anchors are lowercase words joined by hyphens. They must not end in a number, and each one is used once per page. A section without an anchor keeps its automatic id.
- **Email or phone:** `mailto:hello@example.com` or `tel:+1 312 555 0100`. The address must be valid, and a phone number needs 7 to 15 digits. On an item, the item's text becomes the clickable link.

Other addresses are rejected, including outside websites and `javascript:`. The output check also fails on any invalid email or phone link. It fails, too, if Hugo replaced a link it judged unsafe (`#ZgotmplZ`).

The helper validates configuration before building and renders into an isolated temporary destination. Successful builds reconcile only files recorded in the previous build manifest. Existing untracked assets (`.html`, `.js`, `.css`, `.map`) that would otherwise remain in the destination block the build; choose an empty output directory rather than leaving unknown assets in place. Never use a source directory as the output destination.

## Content and delivery review

The workshop deliberately demonstrates testimonial, statistic, and pricing layouts with conspicuous sample notices. The default compositions omit testimonial endorsements. Replace or omit sample people, claims, service areas, and offers before using a site as a real business website. A new name does not approve the other text.

Client contact pages retain the existing accessible form. Its service choices come from the selected preset's `services` section, so the form and the Services page can never disagree; budget choices come from `data/contact.yaml`. Keep budgets in step with any prices you publish. A preview never sends a message. The endpoint accepts a submission only when the deployment declares its own storage and sets `ENQUIRY_ENABLED = "true"`, and it acknowledges receipt only after the durable write succeeds; a client copy is scaffolded with neither, so it cannot write into another site's enquiry store. A Cloudflare Pages Function (`functions/api/contact.js`) provides durable enquiry storage in KV with 90-day retention and IP rate limiting, documented in `docs/cloudflare-setup.md`, and actual receipt remains an external acceptance step.

## Review and verify

```sh
python3 scripts/factory.py
python3 scripts/build.py
python3 scripts/check_site.py
python3 scripts/test_factory.py
python3 scripts/test_from_plan.py
node scripts/test_contact_endpoint.mjs
sh scripts/check_contact.sh
node scripts/check_components.cjs
node scripts/check_workflow.cjs
```

Use the targeted browser checks documented in the README for changed routes. Check narrow screens, keyboard use, both color modes, and a no-JavaScript visit. Performance reports and automated accessibility results apply only to the measured output, never every future composition.

For a client meeting, open the master workshop, choose a business composition, and use the catalog to discuss which sections earn a place. Business demo previews are intentionally contact-disabled; the master header identifies the factory and provides a route back to the catalog. Client copies use their own branding. See [roadmap.md](../roadmap.md) for milestone status and [acceptance.md](acceptance.md) for measured verification limits.
