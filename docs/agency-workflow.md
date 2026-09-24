# Agency storefront, internal factory

The public business sells website design and delivery. The factory is the internal production process: reusable components, deliberate assembly, and consistent checks. Clients should see a site shaped around their business and understand what happens next.

## Two local surfaces

The default build produces the agency site in `public`, with no workshop routes or workshop navigation:

```sh
python3 scripts/build.py --serve --port 1313
```

Open http://127.0.0.1:1313/ to review the agency storefront.

For internal planning, run a separate preview:

```sh
python3 scripts/build.py --workshop --serve --port 1314
```

Open http://127.0.0.1:1314/site-kit/ for the catalog, business presets, and living style guide. This command writes to `public-workshop` and leaves the default configuration and `public` output alone. Rebuild the relevant preview after edits. Keep workshop output local; it is not authenticated or suitable for private client information if hosted. Use the default build for delivery, and keep `data/factory.json` set to `"workshop": false`.

## Delivery cycle

1. **Start from a complete site.** In `/site-kit/`, choose the closest ready-made composition. Its pages, components, and draft copy appear immediately; remove the pages and sections that do not solve a visitor need. A blank plan remains available when no starter fits.
2. **Confirm the smaller site's brief and scope.** Record the audience, visitor goal, existing content, constraints, page list, content responsibilities, exclusions, and who approves the work. Set design direction, fees, and review points in the proposal. Actual timing and prices belong to that agreement.
3. **Prepare the client workspace.** Create an isolated copy with `scripts/new_site.py` using the selected preset. Keep client changes in that copy. Replace starter language with confirmed facts and remove any remaining sample material.
4. **Shape the site.** Apply the client's identity, approved copy, and authentic images. Assemble reusable sections and make project-specific changes where the brief calls for them. The client reviews their own pages, with a clear list of decisions and missing inputs.
5. **Verify and hand over.** Check the generated site and relevant browser journeys, including mobile navigation and contact behavior. Record remaining issues, content approval, ownership, update instructions, and the launch decision. Publication and live integrations require explicit authorization.
6. **Learn from delivery.** Record time spent, revision causes, missing components, and support questions. Bring useful general improvements back into the master deliberately, without copying client information or changing other client sites automatically.

## What belongs where

- **Agency site:** services, illustrative or approved work, scope guidance, the client process, and contact information.
- **Client review:** the client's proposed pages, content questions, scope decisions, and acceptance items.
- **Internal workshop:** component variants, presets, design tokens, build tools, and reusable implementation details.

The current agency is still a demonstration. Preserve fictional-project labels and disabled-contact notices until the relevant facts and delivery are ready. Remove unsupported people, endorsements, results, and turnaround claims from the sales story. Reuse itself does not establish speed savings, profitability, or successful client delivery; measure those through completed projects.

## Low-fidelity project workspace

The workshop homepage opens **Client projects** with a complete-site starter selected by default (the compact local-service composition). Load it to see the pages, sections, and draft copy immediately; remove pages in **Page plan** and sections in **Shape pages and copy**. A working title is optional, and the brief can wait until after the first subtraction pass. **Start with a blank plan** remains available as the second path. Pages and sections can also be added and moved with buttons. Undo restores recent edits during the current session. Reopening a project resumes its last saved stage and page.

The section editor separates missing, draft, and approved copy. Editing a section returns its copy to draft; changing project content clears human review confirmations and the ready-for-design marker. Human review is an explicit operator decision, not an automated accessibility certification. Unknown business facts remain visible in the handoff.

Projects are saved in browser local storage on the current origin (including the port). The status line reports success or failure. Export a JSON backup to move work between browsers or addresses. Import creates a separate project, validates its structure, and clears review confirmations. A Markdown design brief contains the page plan, copy, content states, and open questions. These are planning artifacts, not generated Hugo client sites.

The AI copy control prepares a prompt from the brief and selected section. The planner itself connects to no model or external service. Paste a proposed response, review it, and apply it as draft; proposals are saved separately until applied. Business facts and approval remain under operator control.

The component catalog moved to `/site-kit/catalog/`; the style guide and preset references remain available from it. Exported JSON project plans can now be compiled directly into validated factory presets using `scripts/from_plan.py` (`python3 scripts/from_plan.py export.json --name client-preset --write`). Outside the planner, `scripts/draft_plan.py` drafts a plan from a written brief with the Claude API (a paid call), and `scripts/factory_run.py` goes from a brief or plan to a checked client copy. See the README's **AI and agent tools**. Shared remote storage for the planner and automated launches are not planned; see `roadmap.md`.

### Focused verification

After rebuilding the workshop, run `node scripts/check_workflow.cjs` for isolated browser checks of persistence, exports/imports, review gating, keyboard-friendly reordering, storage failures, competing tabs, and scoped accessibility/overflow. It starts a temporary loopback server and closes it on completion; it does not use or clear the operator's project storage.
