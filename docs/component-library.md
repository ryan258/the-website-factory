# Component library: practical visitor needs

The library now contains **39 component families / 117 reference variants — three layouts per family**. The planner reads the same module registry as the renderer, making all 39 families available under **Shape pages → Section to add**. Existing saved section names remain compatible.

Choose a family to see its purpose and required content before adding a blank section. The new practical families also include copy and accessibility guidance. Section options retain that guidance and link to the corresponding reference layouts. AI prompt preparation includes the component's guidance; it does not connect to a service or create business facts.

| New family | Layouts | Visitor need |
| --- | --- | --- |
| Is this right for you? | Split, stacked, disclosures | Recognize service fit and when to discuss an alternative |
| Included and outside scope | Columns, stacked, disclosures | Understand what is included and what needs separate agreement |
| Preparation checklist | Checklist, ordered, cards | Know what to gather before a conversation or appointment |
| Opening hours | Table, list, cards | Find the regular schedule and exceptions |
| Plan your visit | Details, cards, rows | Understand directions, arrival, and access arrangements |
| Menu or service list | Table, cards, list | Read item details and confirmed price or scope information |
| Events and sessions | Agenda, cards, rows | Find the date, location, and participation conditions |
| Practical policies | Accordion, open, cards | Read relevant approved conditions before committing |
| Terms explained | Definition list, disclosures, cards | Understand unfamiliar terminology |
| Help and support routes | Routes, steps, rows | Choose the appropriate help route |
| Project brief builder | Wizard, sidebar, compact | Organize project details in the current browser tab, then choose an explicit handoff |

These are content components. Event cards do not take bookings, opening hours do not detect live availability, and support links do not create a ticket system. Preparation lists are instructions, not saved task checkboxes. The project brief builder does not save or submit answers; copy, download, and email-draft actions happen only when a visitor chooses them. Replace its example email before using that handoff. Sample content is explicitly illustrative. Layout choice and client-site generation remain separate from the low-fidelity planner's content plan.

## Eight additional families with three layouts each

| Family | Layouts | Visitor need |
| --- | --- | --- |
| Announcements | Cards, rows, spotlight | Understand a temporary change and the next action |
| Booking and next steps | Steps, cards, rows | Know how a request becomes a confirmed appointment |
| Delivery and collection | Cards, definitions, table | Compare fulfilment arrangements and conditions |
| Access and accommodations | Cards, definitions, disclosures | Find specific access information and ask about arrangements |
| Eligibility and requirements | Cards, checklist, disclosures | Understand participation criteria and alternatives |
| Documents and downloads | Cards, rows, table | Identify a resource and its format before opening it |
| Specifications and details | Definitions, table, cards | Read labelled values with units and limitations |
| Updates and changelog | Timeline, cards, rows | Understand dated changes and their effect |

Each family has purpose, copy, and accessibility guidance in the shared registry, plus explicitly illustrative examples. Booking explains the process; it does not schedule an appointment. Delivery explains arrangements; it does not track fulfilment. Announcement and update samples are static content. Document samples link to existing HTML reference pages, with HTML format labels, rather than pretend downloadable files. Replace the examples with approved content and real resource destinations before use.

## Original families now have three layouts

The existing 31 families now also have three layouts. This adds 31 layout options: one for each of the 29 former two-layout families, and two for the project brief builder. Hero already had three. Existing variant names and preset selections are retained. All examples use the same content across layouts so the comparison shows the structural difference.

| Family | Layouts |
| --- | --- |
| First impression | split, centered, compact |
| Services | cards, rows, spotlight |
| Selected work | gallery, editorial, tiles |
| Process | steps, rows, timeline |
| About | split, editorial, centered |
| People | cards, rows, compact |
| Questions | accordion, open, columns |
| Scope & pricing | cards, rows, table |
| Service areas | cards, rows, list |
| Client voices | quotes, featured, list |
| At a glance | strip, cards, rows |
| Next step | band, quiet, centered |
| Get in touch | panel, compact, rows |
| Useful reading | cards, rows, directory |
| Compare options | table, cards, rows |
| Before & after | panels, stacked, narrative |
| Features & capabilities | grid, split, rows |
| Proof & partners | grid, inline, list |
| Timeline & milestones | vertical, cards, rows |
| Bento highlights | mosaic, compact, rows |
| Is this right for you? | split, stacked, disclosures |
| Included and outside scope | columns, stacked, disclosures |
| Preparation checklist | checklist, ordered, cards |
| Opening hours | table, list, cards |
| Plan your visit | details, cards, rows |
| Menu or service list | table, cards, list |
| Events and sessions | agenda, cards, rows |
| Practical policies | accordion, open, cards |
| Terms explained | definitions, disclosures, cards |
| Help and support routes | routes, steps, rows |
| Project brief builder | wizard, sidebar, compact |

The project brief forms use unique IDs and label/help references for each instance. Wizard, sidebar, and compact arrangements share the same three-step validation and explicit handoff behavior. No field is removed in the compact layout.

## Comparing layouts

At `/site-kit/catalog/`, open a family and choose **Full width** or **Compare layouts**. All variants remain visible in both views. Comparison uses two columns at viewport widths of 1200px and above, then stacks on smaller screens. Native radio controls work without JavaScript and support keyboard selection. The added layouts use container queries where appropriate so their inner layouts adapt to the available comparison width. The existing families retain their layouts and selected preset content.

## Contracts and reuse

`data/modules.json` defines variants, required fields, optional per-item required fields and allowed choices. Delivery and specification items require a value; document items require a value, URL, and link label; update items require a date label. Menu items require a price/scope value; events require when/where; support routes require a valid local URL and meaningful link label; service-fit and inclusion entries require a supported group. `scripts/factory.py` rejects missing or invalid structured values before building. The project brief module is a human-selected feature and is excluded from AI-drafted plans.

`data/examples.json` supplies catalog samples. `layouts/partials/factory/practical.html` renders the earlier practical families, and `collection.html` renders the eight additions through the same module entry point used by client compositions. Add a module to a selected preset's ordered sections and supply its required content to use it in a built client site. No new sections were automatically added to the agency storefront.

## Focused checks

Build the workshop with `python3 scripts/build.py --workshop`, then run `node scripts/check_components.cjs`. It checks all 117 layouts across 39 families, scoped accessibility in both light/dark themes and both preview arrangements, widths 320/900/1440, comparison columns and mobile stacking, unique instance IDs, independent brief-form completion and reset, keyboard disclosures and comparison radios without JavaScript, all 39 planner choices, and saved layout selections using isolated browser storage. `python3 scripts/test_three_layouts.py` validates compilation and exact example-content preservation for all 117 layouts. `python3 scripts/test_component_expansion.py` validates compilation and content preservation for all 24 added layouts and rejects omitted structured requirements. `python3 scripts/test_schemas.py SchemaTests` checks schema currency and existing preset compatibility. It starts and closes a temporary local server. These checks do not establish real business-content approval or assistive-technology acceptance.
