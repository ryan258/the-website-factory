# Component library: practical visitor needs

The library now contains **30 component families / 61 reference variants**. The planner reads the same module registry as the renderer, making all 30 families available under **Shape pages → Section to add**. Existing saved section names remain compatible.

Choose a family to see its purpose and required content before adding a blank section. The new practical families also include copy and accessibility guidance. Section options retain that guidance and link to the corresponding reference layouts. AI prompt preparation includes the component's guidance; it does not connect to a service or create business facts.

| New family | Layouts | Visitor need |
| --- | --- | --- |
| Is this right for you? | Split, stacked | Recognize service fit and when to discuss an alternative |
| Included and outside scope | Columns, stacked | Understand what is included and what needs separate agreement |
| Preparation checklist | Checklist, ordered | Know what to gather before a conversation or appointment |
| Opening hours | Table, list | Find the regular schedule and exceptions |
| Plan your visit | Details, cards | Understand directions, arrival, and access arrangements |
| Menu or service list | Table, cards | Read item details and confirmed price or scope information |
| Events and sessions | Agenda, cards | Find the date, location, and participation conditions |
| Practical policies | Accordion, open | Read relevant approved conditions before committing |
| Terms explained | Definition list, disclosures | Understand unfamiliar terminology |
| Help and support routes | Routes, steps | Choose the appropriate help route |

These are content components. Event cards do not take bookings, opening hours do not detect live availability, and support links do not create a ticket system. Preparation lists are instructions, not saved task checkboxes. Sample content is explicitly illustrative. Layout choice and client-site generation remain separate from the low-fidelity planner's content plan.

## Contracts and reuse

`data/modules.json` defines variants, required fields, optional per-item required fields and allowed choices. Menu items require a price/scope value; events require when/where; support routes require a valid local URL and meaningful link label; service-fit and inclusion entries require a supported group. `scripts/factory.py` rejects missing or invalid structured values before building.

`data/examples.json` supplies catalog samples. `layouts/partials/factory/practical.html` renders the new families through the same module entry point used by client compositions. Add a module to a selected preset's ordered sections and supply its required content to use it in a built client site. No new sections were automatically added to the agency storefront.

## Focused checks

Build the workshop with `python3 scripts/build.py --workshop`, then run `node scripts/check_components.cjs`. It checks the 20 new variants, scoped accessibility in light/dark themes, widths 320/900/1440, keyboard disclosures without JavaScript, planner choice coverage, and a saved-selection round trip using isolated browser storage. It starts and closes a temporary local server. These checks do not establish real business-content approval or assistive-technology acceptance.
