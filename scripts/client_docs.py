"""Generate instructions for capabilities that actually ship with a client copy."""
import json


def write(destination, name, preset):
    capabilities = dict(version=1, name=name, preset=preset, workshop=False, standalone=True,
                        commands=['status', 'open', 'check', 'backup', 'handover'],
                        publication='owner-controlled', approval_inherited=False)
    (destination / 'factory-capabilities.json').write_text(json.dumps(capabilities, indent=2) + '\n')
    intro = f'''# {name}

Independent client draft, based on preset `{preset}`. Python 3.11+, the pinned
Hugo Extended and Dart Sass are required. Run commands from this folder.

```sh
python3 scripts/doctor.py
python3 scripts/setup.py
./wf status
./wf open
```

`open` builds a checked preview and serves it locally. `status` reports content
gaps and whether the saved source still matches the last build. No command here
publishes the site or enables intake.

## Edit and check

Edit the selected JSON file in `data/presets/` for page titles, descriptions,
sections and copy. Edit `data/site.yaml` for the brand, contact details and shared
footer. Detail pages keep their own Markdown front matter in `content/`.
Composition metadata comes from the preset on every build.

```sh
./wf check
./wf backup
./wf handover
```

Install optional quality tools with `npm ci` and `python3 -m pip install -r
requirements-dev.txt`. `npm test` runs the client checks; it requires a current
build. Claim checks are strict: unresolved samples remain drafts. Add an approval
only after the owner confirms the exact wording; copies inherit no approvals.

Backups are source archives under `reports/backups/`. Keep a separate copy for
machine-loss recovery. `./wf restore ARCHIVE DESTINATION` restores into a new folder.

The master workshop, specialist adapters and evaluation fixtures are not included.
`factory-capabilities.json` lists this copy's supported scope. A client copy can
create another independent copy of its retained preset with `scripts/new_site.py`.

## Release and recovery

Read `docs/cloudflare-setup.md` for owner-controlled hosting and form setup. A
public build requires a real domain, confirmed content and no unresolved claims.
Build receipts record source/output hashes and effective indexing/form settings.
Handover is automated evidence; it does not certify accessibility, factual truth,
image rights or live delivery. Check changed visitor journeys and retain useful
evidence for unchanged components.

If a build fails, keep the sources, read the named field or file, repair it and
rebuild. Never delete modified output to silence an ownership warning; use a fresh
output directory or preserve those edits first. For a storage failure, export the
browser project before leaving that page.
'''
    (destination / 'README.md').write_text(intro)
    for filename in ('starter-guide.md', 'factory-guide.md', 'agency-workflow.md', 'component-library.md'):
        (destination / 'docs' / filename).write_text(intro)
    (destination / 'AGENTS.md').write_text('''# Client site rules

Read README.md and factory-capabilities.json. Preserve owner edits. Validate before
hand editing with scripts/factory.py; use scripts/claims.py --strict for full-site
claim scope. No invented facts or inherited approvals. Keep draft noindex and intake
off until the owner explicitly authorizes release. Do not stage, commit, push,
deploy, enable forms, contact anyone or call a paid provider without authorization.
The optional MCP server is scripts/mcp_server.py. Its tool descriptions state scope
and side effects. No factory checkout or GitNexus index is required here.
''')
