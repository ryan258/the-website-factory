# Sculpt a client website

The master includes four fictional business compositions and a visual catalog at `/site-kit/`. The catalog renders the same components as the client sites. It is a review surface, not an additional client page.

## Start a separate copy

```sh
python3 scripts/new_site.py ../cedar-studio --name "Cedar Studio" --preset contractor
```

Choose `agency`, `contractor`, `consultant`, or `local-service`. The destination must not exist. Copies omit the workshop, unused presets, pages outside the selected composition, unrelated agency project images, generated output, dependencies, Git history, and historical acceptance evidence. Every copy starts with disabled delivery, `noindex`, an invalid example domain, and sample content.

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

`data/modules.json` documents each module's variants, required fields, and page dependencies. The work module requires the work page. Image references must resolve to local assets. Module links currently support local page paths only; external links and arbitrary fragments are intentionally rejected until they have a defined validation contract.

The helper validates configuration before building and renders into an isolated temporary destination. Successful builds reconcile only files recorded in the previous build manifest. Existing untracked HTML that would otherwise remain as a stale page blocks the build; choose an empty output directory rather than deleting unknown files. Never use a source directory as the output destination.

## Content and delivery review

The workshop deliberately demonstrates testimonial, statistic, and pricing layouts with conspicuous sample notices. The default compositions omit testimonial endorsements. Replace or omit sample people, claims, service areas, and offers before using a site as a real business website. A new name does not approve the other text.

Client contact pages retain the existing accessible form. Its service choices come from `data/services.yaml`, and budget choices from `data/contact.yaml`. Keep those in sync with offered services. A preview never sends a message. Netlify is the only implemented delivery provider, and actual receipt remains an external acceptance step.

## Review and verify

```sh
python3 scripts/factory.py
python3 scripts/build.py
python3 scripts/check_site.py
python3 scripts/test_factory.py
```

Use the targeted browser checks documented in the README for changed routes. Check narrow screens, keyboard use, both color modes, and a no-JavaScript visit. Performance reports and automated accessibility results apply only to the measured output, never every future composition.

For a client meeting, open the master workshop, choose a business composition, and use the catalog to discuss which sections earn a place. Business demo previews are intentionally contact-disabled; the master header identifies the factory and provides a route back to the catalog. Client copies use their own branding. See [roadmap.md](../roadmap.md) for milestone status and [acceptance.md](acceptance.md) for measured verification limits.
