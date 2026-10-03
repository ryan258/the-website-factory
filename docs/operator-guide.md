# Factory operator guide

The factory turns a selected preset or saved page plan into an independent Hugo
site. Use the short launcher to create, resume, check and recover local work.
The October changes have passed owner-run verification (`python3 scripts/verify_review.py`).

## Start and resume

Python 3.11+, the pinned Hugo Extended and Dart Sass are required. Optional test
tools are installed through the existing requirements and package lockfiles.

```sh
./wf new
./wf status
./wf open
```

`new` reuses the guided, lettered setup. It creates a separate destination that
must not exist. Use `./wf new ../my-site --name "My Site" --preset creator-writer`
when the choices are already known. `open` builds and serves the current source
on localhost. In the master, use `./wf open --workshop` for the planner.
These commands perform local work. Nothing publishes or enables intake.

For a persistent shell shortcut, an optional alias is:

```sh
alias wf='./wf'
```

This works from a factory or client project directory. No shell profile has been
changed automatically.

## Edit the appropriate source

| Subject | Authority |
| --- | --- |
| Composition, page title and description, copy and section order | Selected JSON in `data/presets/` |
| Brand, shared contact details, navigation labels, fonts and colors | `data/site.yaml` |
| Detail pages and their metadata | Retained Markdown in `content/` |
| Form budget choices | `data/contact.yaml` |
| Indexing, language and form rendering | `hugo.toml`, with supported explicit build overrides |
| Per-deployment intake | Owner-controlled `wrangler.toml` and hosting configuration |

The planner carries structured section content into its export. Its default view
expands one section; “Show all section fields” restores the longer editor. Layout
selectors and item controls edit the same content contract used by the compiler.
Copy changes return the affected section to draft. Redo is available after undo.

“Save project file” uses the browser's file picker where supported and otherwise
downloads a portable backup. Browser storage remains tied to its origin. A file
handle is remembered for this session only; later sessions use import or the picker.
This is explicit saving, not automatic cloud synchronization.

Three creator starters cover a portfolio, writing and audio project. They use
`site_type: "creator"` and `contact_mode: "off"`, require only a home page and do
not acquire services or an inquiry form during compilation. `email` and `link`
modes omit the built-in inquiry form too; put the chosen destination in section
actions. Credential-free HTTPS links are supported for buttons and resource items.
Unknown creator facts remain “To be confirmed.”

## Review changed content and make a release artifact

```sh
./wf check
./wf status
./wf handover
```

`check` builds, checks generated output and runs strict whole-site claims and
contrast checks. It is not the full regression suite. Draft previews can build
with open content questions; strict checks tell you what remains.

`status` compares current sources with the last build receipt and lists fields
that differ from the most recent owner content review. Unchanged field evidence
is retained. Pattern-based claims checking covers only recognized categories;
zero matches does not establish that every assertion is true.

After actually reviewing the changed facts, destinations and retained asset rights,
the owner can record that decision:

```sh
./wf approve --by Ryan
```

This is an explicit content decision, not an automated approval. It records the
reviewer, time and current field/asset hashes in `data/content-review.json`. It
refuses open detected claims and placeholders. Confirm exact claim wording in
`approved_claims` only when supported by the owner; retain the source evidence
with the project. An edit invalidates the changed fields. New client copies drop
the review and all inherited claim approvals.

An indexable build requires current content review, no open detected claims and no
unresolved placeholders. It also requires a real domain and a valid visitor path
for inquiry mode. The internal workshop cannot become an indexable release.
When the built-in form is rendered on, the deployment file must also enable
intake; an external form destination uses its separate owner-configured path.
Release authorization remains separate from content review.

`.factory-receipt.json` binds source hashes, settings, tool pins and output hashes.
`factory-release.json` exposes only a version and opaque release ID. Cloudflare
middleware hides the private dotfiles. Handover fails readiness when source or
recorded output has changed. A missing old receipt is fixed by rebuilding.

After an explicitly authorized deployment, a read-only identity check is:

```sh
python3 scripts/smoke.py https://your-domain.example --expected-release-file public/factory-release.json
```

The check sends GET requests. It does not demonstrate form intake or send an
enquiry. The production workflow now compares the uploaded release ID after its
owner-authorized publish step. It still requires the owner-controlled workflow
dispatch; no deployment occurred during remediation.

## Backup and recover

```sh
./wf backup
./wf restore reports/backups/ARCHIVE.zip ../recovered-site
./wf preview-plan saved-project.json ../draft-preview
```

Backups contain source, docs, schemas and supporting project metadata, excluding
Git history, local environments and generated sites. Restore validates paths and
requires a new destination. Keep copies off the machine when that level of recovery
is needed. Previewing a saved plan creates a checked client and serves it; it does
not make another API request. Direct preview from the browser editor remains a
future local-bridge feature.

Paid drafting checks the destination and required build executables first. Original
model text is retained under ignored `reports/drafts/` before conversion. The brief
workflow also reserves a neighboring `.draft.json` recovery file. Oversized content
is rejected instead of silently shortened. A failed provider call may leave an
empty reserved recovery file; inspect it before explicitly removing it or choosing
another destination. No automatic retry or paid repair loop runs.

## Specialist verticals

The contractor and restaurant adapters require their sibling source checkouts.
The contractor uses the same interpreter as the launcher and requires the pinned
PyYAML in `requirements-vertical.txt`. The launcher validates dependencies and
options before copying, completes the adapter in a temporary directory, checks
the scaffold receipt contract and only then reserves the final destination.
Failure removes only the temporary or exclusively created destination.

Generic client copies include their own README, agent instructions, capability
manifest, schemas and `wf` launcher. Their docs describe the retained preset and
do not offer a missing master workshop or specialist launcher.

## Verification and evidence

```sh
python3 scripts/verify_review.py
```

This is the owner-run command for this patch. It stops at the first failed gate
and writes logs under `reports/review-verification/`. `--full` adds the remaining
established local gates. It makes no live model request and does not deploy.
The separate Pages emulator integration command remains `sh scripts/check_contact.sh`;
it may download its pinned tooling and is not run implicitly by the targeted runner.

Accessibility evidence is scoped to the checks and journeys actually exercised.
Use bounded checks for changed interactions and retain unchanged evidence. Earlier
test counts in `docs/acceptance.md` are historical until this patch is verified.
