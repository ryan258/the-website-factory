# October project review remediation

Implementation now addresses the sixteen correction findings and adds a bounded
set of creator workflow improvements. The owner's local verification run
`20261003T230404161102Z` passed all 21 default review commands, including both
builds and the two planner browser suites. The agent inspected the saved results
without rerunning tests or builds. Changes remain uncommitted. No paid model call,
live integration or deployment was performed by the remediation work.

The original [project review](project-review-2026-10-03.md) remains the evidence for
the earlier state. [The operator guide](operator-guide.md) describes the new commands
and source contracts.

## Correction coverage

All rows below describe implemented corrections covered by the passing default
review run. That evidence is bounded to those checks; external and platform-specific
acceptance remains separate, as recorded below.

| Finding | Implementation | Verification focus |
| --- | --- | --- |
| F01 Claims scope | MCP slug checks, handover and post-copy plan review include shared data and retained Markdown; candidate-object checks label preset-only scope. | A shared-data price appears in every full-site interface. |
| F02 Release gating | Indexable builds require whole-site claims, placeholder clearance and current owner content review; client checks use `--strict`. | Draft is allowed; release stops on unresolved content. |
| F03 Stale handover | New build receipt records source/settings/artifacts; handover verifies freshness and output integrity. | Editing source or generated HTML makes evidence stale. |
| F04 Missing gates | Shared scaffold and remediation regressions join npm tests; browser fidelity joins CI. | Both affected contracts run in advertised gates. |
| F05 Vertical dependency | Interpreter-specific PyYAML preflight, normalized destinations, staged adapter completion and receipt contract checks. | Missing dependency writes no client; adapter failure rolls back staging. |
| F06 Malformed MCP | JSON-RPC envelope and nested preset shape checks precede dispatch/semantic traversal. | Bad request followed by ping succeeds in the same process. |
| F07 Creation evidence | Both preset and plan paths build; results expose created/validated/built/checked states. | Failed build retains the created copy and reports build failure. |
| F08 Function headers | JSON, HTML errors, redirects and method responses set explicit security headers. | Header checks use actual Function responses. |
| F09 Contact feedback | Stable failure codes and tailored text preserve inputs; stored enquiries can notify through `waitUntil`. | Slow notification does not delay durable acknowledgement. |
| F10 Client package | Generated client docs, AGENTS, capability manifest, launcher and schemas; retained guides describe only delivered capabilities. | A second-generation copy is independent and carries no approval. |
| F11 Content authority | Composition metadata reads the preset at render time; detail front matter is preserved; counts/floor/evidence docs reconciled. | Edit preset metadata after scaffolding, then rebuild. |
| F12 Accessibility claims | Roadmap no longer equates automated axe findings with conformance; review guidance is bounded to changed journeys. | Documentation accurately scopes evidence. |
| F13 Output locking | Persistent Unix/Windows lock beside output, acquired before inventory reads or cleanup; failure is closed; manifest writes use exclusive temporary files. | Contention, lock errors, unchanged refused destinations and owned-output recovery. |
| F14 Creator contracts | Explicit creator/contact modes flow through schema, compiler, renderer and output checker; safe HTTPS actions/resource links supported. | Creator pages acquire neither services nor inquiry form. |
| F15 Truth and samples | Unused demo sections removed from active preset; field/asset review digests cover changes outside regex claims; scanner limits remain explicit. | Exact changed fields invalidate content review; no facts approved automatically. |
| F16 Release identity | Public opaque ID plus smoke comparison; authorized deployment workflow checks uploaded identity. | A healthy but old deployment fails the expected-ID check. |

## Immediate creator improvements

The new `wf` launcher exposes status, guided creation, preview, checks, source
backup/restore, handover, content review and saved-plan preview. The status view
lists stale evidence, open claims and changed review fields.

The planner opens one section at a time, supports explicit item controls and
layout selection, groups short typing bursts for undo, adds redo, reduces repeated
save announcements and can save a project file through supported browser pickers.
Portfolio, writer and audio starters retain explicit unknowns. Shared TOML parsing
sets the Python floor to 3.11. Paid drafts preserve original text, reject oversized
results and expose an output-token bound. Enquiry reads now fail clearly on partial
data instead of exporting an apparently complete subset.

## Enhancement catalog disposition

The review's enhancement catalog mixes fixes, bounded improvements and substantial
future capabilities. It is retained without claiming that every finish condition
was met in this patch.

| IDs | Current coverage | Remaining scope |
| --- | --- | --- |
| E01–E02 | Short commands and actionable source/build/content status. | Cross-project saved defaults and inventory UI. |
| E03 | Saved-plan CLI preview. | Direct revision-bound preview from the browser without an export step. |
| E04–E05 | Focused editor, variants, item controls and typed basic fields. | Asset picker and full contract-derived field descriptions. |
| E06–E07 | Explicit file saving, source backup/restore, redo and typing groups. | File-backed autosave bridge, named checkpoints and cross-origin recovery UI. |
| E08–E09 | Changed-field queue and revision-bound content review; stale build rejection. | Separate evidence scopes for interaction review and externally confirmed acceptance. |
| E10–E11 | Three creator starters and inquiry/email/link/off modes. | More visitor-goal starters and declarative signup/booking form schemas. |
| E12–E13 | Retained asset hashes enter content review. | Import/optimization UI, rights/source ledger, logo/favicon and visual identity controls. |
| E14–E15 | Configured HTML language, preset metadata authority and optional `seo_title` rendering. | Translated controls/pages, glyph verification, per-page sharing images and redirect management. |
| E16 | Reviewer/date/field evidence complements legacy exact-text claims. | Source-linked supplied/sample/confirmed/expired fact records. |
| E17–E20 | Shared source/settings/receipt and locking services; typed editor reuse of module requirements. | Full browser module separation, versioned migrations, pinned schema identity and unified YAML parsing. |
| E21 | Accurate creation states, scope labels, annotations and safer request contracts. | Typed output schemas, resource discovery and reusable machine workflows. |
| E22 | Destination/tool preflight, original-result recovery, output budget and no silent clipping. | Version-exact tool preflight and optional bounded repair; no automatic paid retries. |
| E23 | Offline reports expose requested/evaluated/missing counts and completeness; `--require-complete` fails partial coverage. | Broader independent fixtures, repetitions, usefulness and cost assessment. |
| E24–E25 | Independent client package and existing scaffold-origin receipt. | Optional client CI and cross-client maintenance proposals. |
| E26 | Partial reads fail without writing a misleading export; background notification failure is logged. | Selected-record deletion, notification health receipts and secondary-copy retention workflows. |
| E27–E28 | Missing gates wired, new local regression cases, concise operator guide and current evidence status. | Shared check manifest, expanded visual/assistive-tech evidence and source/media license inventory. Any new code-sharing license remains the owner's decision. |

## Verification record

`python3 scripts/verify_review.py` passed all 21 commands in owner-run verification
`20261003T230404161102Z`. Its logs and `results.json` are retained locally under
`reports/review-verification/20261003T230404161102Z/`. This includes affected local
tests, two builds, lint and both planner browser suites; the browser fidelity run
covered 11 starter exports. The optional `--full` extension was not run. No repeat
run is needed for the acceptance/remediation documentation updates alone.

Owner-run verification on October 3 passed the remediation, shared scaffold and
plan compiler gates, then stopped at plan fidelity (run
`20261003T222859150905Z`). The Python fixture omitted creator/contact modes carried
by the real planner, causing business-default sections to be added. The fixture
now includes those fields; Python and browser fidelity checks explicitly compare
the modes, and Python also checks exact page order and membership.

The next owner run (`20261003T225219983036Z`) passed the first six gates, including
Python plan fidelity, schemas and claims, then stopped at MCP validation. Its
schema guard suppressed specific factory error codes for validly shaped but
invalid values. MCP validation now stops early only for schema type errors and
otherwise returns both schema and factory diagnostics. The regression also checks
the variant field pointer, repair hint, malformed-type rejection and subsequent
session ping. The next owner run confirmed these checks passed.

Run `20261003T225818408086Z` passed gates 1–8, including MCP and handover, then
reported seven factory failures: five unchanged-destination assertions found a
new lock file inside output, one expected the established contention message,
and one exceeded the workshop planner's previous 10,000-byte gzip budget.
Locks now use a canonical-destination hash in a persistent sibling file, ignored
by Git, so refusal does not add files to output. Contention has its specific
message again; the concurrency regression checks release and output creation too.
The expanded workshop editor has a 15,000-byte gzip budget (its current source
measured 12,516 bytes gzip before minification); public JavaScript retains its
5,000-byte limit. A regression covers the workshop-only exception and both limits.
The final run above passed these corrections and all remaining default gates.

Future enhancement work should use this passing state as its baseline. Live deployment, actual
intake delivery, paid-model usefulness, Windows execution and assistive-technology
acceptance remain separate evidence. No stage, commit, push, deployment, form
enablement, provider call or approval was performed by the remediation work.
