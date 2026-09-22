# Low-fidelity workflow — local verification

2026-09-22. This records the planning prototype, not production readiness or client acceptance.

Implemented at `/site-kit/`: projects, editable briefs, ordered page plans, section wireframes and copy, explicit draft/approval state, actionable content checks, human review, design handoff, session undo, browser saving, JSON backup/import, and Markdown brief export. The component reference is at `/site-kit/catalog/`.

Targeted verification uses `node scripts/check_workflow.cjs` with isolated browser storage and a temporary local server. Coverage includes saved copy and section order across reloads; resume at the saved stage; undo after reopening; literal HTML in copy; backup download/import; malformed-import refusal; missing-content gating; revoking review and readiness after edits; competing-tab protection; enforcing the 2 MB backup limit by refusing and rolling back oversized edits while guaranteeing round-trip importability; and visible storage failure with export available. Scoped axe checks cover the five stages, with a separate dark-mode editor check; overflow is checked at 320, 900, and 1440 pixels.

The actual existing port-1314 preview was refreshed and exercised with a clearly named fictional walkthrough project. Its brief, one-page plan, and sample copy are saved in that browser. Human review checkboxes were left unconfirmed. A visual check identified inherited dark-mode paragraph colors; the editor now explicitly maintains readable neutral text.

Public and workshop builds passed their generated-output checks. The public build omits workshop routes and editor assets. No full project suite, screen-reader assessment, real client acceptance, deployment, or live form test was performed.

Limits: saves belong to the current browser and origin; exports are needed for portable backups. Undo is session-local. AI assistance prepares a prompt and accepts a pasted proposal; no model is connected. Handoff exports a plan, not a generated client website. Visual design and implementation accessibility still require their own reviews.
