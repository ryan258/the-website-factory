#!/usr/bin/env python3
"""Write a plain Hugo copy of this site for handover, with none of the factory attached.

  python3 scripts/eject.py ../client-delivery            # or: ./wf eject ../client-delivery
  python3 scripts/eject.py ../client-delivery --draft    # allow open claims and "To be confirmed"

The copy needs only Hugo Extended and Dart Sass (`hugo --minify`). It has no Python, no module
registry, no schemas, no planner and no launcher. Before it is kept, the copy is built with plain
Hugo and compared with this project's own build: any difference in the generated site (receipt files
aside) deletes the copy and fails. After ejecting, the new folder is the source of truth; changes here
no longer reach it.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

KEEP_DIRS = ('assets', 'content', 'data', 'functions', 'layouts', 'static')
KEEP_FILES = ('hugo.toml', 'wrangler.toml', '.hugo-version', '.sass-version')
KEEP_DOCS = ('acceptance.md', 'handover.md')
# Factory-only files, removed from the copy. The workshop templates and styles are unused by a client site.
DROP = ('data/modules.json', 'data/examples.json', 'data/tones.json', 'content/site-kit',
        'layouts/_default/kit.html', 'layouts/_default/catalog.html', 'layouts/_default/style-guide.html',
        'layouts/_default/composition.html', 'assets/js/workflow.js', 'assets/css/workflow.css',
        'assets/scss/workshop.scss', 'assets/scss/pages/_workshop.scss', 'assets/scss/pages/_style-guide.scss')
RECEIPTS = ('.factory-build.json', '.factory-receipt.json', 'factory-release.json')
REGISTRY_VAR = '{{ $registry := index hugo.Data.modules $m }}'

# Comments in kept files that point at factory scripts the copy does not have.
COMMENT_FIXES = (
    ('layouts/partials/url.html', '; scripts/factory.py has validated them', ''),
    ('layouts/partials/factory/module.html',
     ' Presets themselves are link-checked by scripts/factory.py.', ''),
    ('assets/scss/abstracts/_variables.scss',
     '// Accent per preset tone. Must match data/tones.json (scripts/test_factory.py checks), which\n'
     '// scripts/factory.py validates presets against and copies into a scaffolded data/site.yaml.\n',
     '// Accent per preset tone, used by the .tone-<name> classes.\n'),
)
WRANGLER_BUILD = """# --- Building --------------------------------------------------------------
# Build locally with `hugo --minify`, then upload with `npx wrangler pages deploy public`.
# If Cloudflare builds from a Git repository instead:
#   Build command:    hugo --minify
#   Output directory: public
#   HUGO_VERSION={hugo}  DART_SASS_VERSION={sass}
"""
DEPLOYING = """# Deploying {name}

You need your own Cloudflare account, a Pages project and, for the contact form, a KV namespace.
Nothing here is shared with whoever built the site.

## 1. Build

```sh
hugo --minify          # writes public/
```

Needs Hugo Extended {hugo} and Dart Sass {sass}.

## 2. Create the Pages project and publish

```sh
npx wrangler login
npx wrangler pages project create <project-name> --production-branch main
npx wrangler pages deploy public --project-name <project-name>
```

Open the `.pages.dev` address it prints and look at the site before attaching your domain.

## 3. Attach your domain

Dashboard → Workers & Pages → your project → Custom domains → Set up a custom domain.
For search engines to index the site, rebuild for the real address with indexing on:

```sh
HUGO_PARAMS_NOINDEX=false hugo --minify --baseURL https://example.com/
```

## 4. The contact form (optional)

The form is off until all three are done. Do them together, or visitors see errors.

1. `npx wrangler kv namespace create ENQUIRY`, then put its id in `wrangler.toml` and uncomment the
   `[[kv_namespaces]]` block.
2. Uncomment `[vars] ENQUIRY_ENABLED = "true"` in `wrangler.toml`. Without it the endpoint refuses every
   message, on purpose.
3. Build with the form switched on, then deploy:

```sh
HUGO_PARAMS_FORMENABLED=true HUGO_PARAMS_NOINDEX=false hugo --minify --baseURL https://example.com/
npx wrangler pages deploy public --project-name <project-name>
```

The form stores each enquiry in KV for 90 days and sends no email. To be told about new ones, add a
chat or automation webhook: `npx wrangler pages secret put NOTIFICATION_WEBHOOK --project-name <project-name>`.
Also set `RATE_LIMIT_SALT` the same way. Update the privacy page to match what the form stores.

Send yourself a real test enquiry, then read it back:

```sh
npx wrangler kv key list --binding ENQUIRY --remote --prefix enquiry:
npx wrangler kv key get --binding ENQUIRY --remote "<key from the list>"
```

Do not skip the test. A form that looks fine and drops messages is worse than none.

## 5. Mail on your domain

Cloudflare Email Routing (Compute → Email Service → Email Routing) forwards mail sent to your domain
to an inbox you already have. It does not send mail. If you already use a hosted mailbox, leave your
mail records alone.
"""

README = """# {name}

A static website built with [Hugo](https://gohugo.io). Nothing else is required to build or change it.

## Requirements

- Hugo Extended **{hugo}**
- Dart Sass **{sass}** (the standalone `sass` command, on your PATH)

## Build and preview

```sh
hugo server          # preview at http://localhost:1313, rebuilds when you save
hugo --minify        # the real build, written to public/
```

## Where things are

| To change | Edit |
| --- | --- |
| Business name, contact details, navigation, footer, colors, fonts | `data/site.yaml` |
| Page titles, section order, and all visible copy | `data/presets/{preset}.json` |
| Contact form choices | `data/contact.yaml` |
| Detail pages (services, projects) | Markdown files in `content/` |
| Images | `assets/images/` (referenced by path from the files above) |
| How a section looks | `layouts/partials/factory/` and `assets/scss/pages/_factory.scss` |

### How a page is put together

`data/presets/{preset}.json` has two parts. `pages` lists each page and its sections in order; each
section names a `module` (the kind of section), a `variant` (its layout) and a `content` key.
`sections` holds the copy for each content key. To reorder a page, reorder its `sections` list. To
add a section, add an entry there and its copy under `sections`.
`layouts/partials/factory/module.html` draws each module and variant. Pick the one you want
and read its branch to see which fields it uses. `data/factory.json` names the file above.

## Putting it online

The built `public/` folder is plain files and works on any static host. `docs/cloudflare-setup.md`
has the steps for Cloudflare Pages, the contact form, your domain and search-engine indexing. The site
is built with `noindex` on until you turn it off there.

## What this folder does not contain

It no longer has the build helper, tests, claim checks or planning tools it was made with. They are
not needed to run the site. Check links and wording yourself before you publish changes.
"""


def tree(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file() and p.name not in RECEIPTS}


def copy_sources(destination):
    for name in KEEP_DIRS:
        shutil.copytree(ROOT / name, destination / name, symlinks=False,
                        ignore=shutil.ignore_patterns('.DS_Store', '__pycache__'))
    for name in KEEP_FILES:
        if (ROOT / name).is_file():
            shutil.copy2(ROOT / name, destination / name)
    (destination / 'docs').mkdir()
    for name in KEEP_DOCS:
        if (ROOT / 'docs' / name).is_file():
            (destination / 'docs' / name).write_text(
                '> Evidence recorded before handover, with build and test tools that are not part of this folder.\n\n'
                + (ROOT / 'docs' / name).read_text())
    for name in DROP:
        path = destination / name
        shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)
    # Same selection the build applies: only the selected preset's pages, and detail pages something links to.
    import factory
    import json
    import site_state
    preset = site_state.selected(ROOT)
    for path in (destination / 'content').iterdir():
        if path.is_dir() and path.name not in preset['pages']:
            shutil.rmtree(path)
    factory.prune_unlinked_details(destination / 'content', preset)
    for other in (destination / 'data/presets').glob('*.json'):
        if other.stem != json.loads((ROOT / 'data/factory.json').read_text())['preset']:
            other.unlink()
    pins = dict(hugo=(ROOT / '.hugo-version').read_text().strip(), sass=(ROOT / '.sass-version').read_text().strip())
    for name, old, new in COMMENT_FIXES:
        path = destination / name
        text = path.read_text()
        if old not in text:
            raise ValueError(f'{name} no longer contains the comment this script rewrites; update eject.py.')
        path.write_text(text.replace(old, new))
    wrangler = destination / 'wrangler.toml'
    text = wrangler.read_text()
    wrangler.write_text(text[:text.index('# --- Building')].rstrip('\n') + '\n\n' + WRANGLER_BUILD.format(**pins)
                        if '# --- Building' in text else text.rstrip('\n') + '\n\n' + WRANGLER_BUILD.format(**pins))
    module = destination / 'layouts/partials/factory/module.html'
    lines = module.read_text().split('\n')
    # The registry check is the only render-time use of data/modules.json: line 1 declares it, lines 2-4 test with it.
    if not lines[0].endswith(REGISTRY_VAR) or not all('$registry' in line for line in lines[1:4]) or '$registry' in '\n'.join(lines[4:]):
        raise ValueError('module.html no longer starts with the registry check this script removes; update eject.py.')
    module.write_text('\n'.join([lines[0][:-len(REGISTRY_VAR)]] + lines[4:]))
    name, slug = preset['name'], json.loads((ROOT / 'data/factory.json').read_text())['preset']
    (destination / 'README.md').write_text(README.format(
        name=name, preset=slug, **pins))
    (destination / 'docs/cloudflare-setup.md').write_text(DEPLOYING.format(name=name, **pins))
    (destination / '.gitignore').write_text('public/\nresources/\n.hugo_build.lock\n.DS_Store\n')


def eject(destination, draft=False):
    import build
    import factory
    import site_state
    destination = Path(destination).expanduser().absolute()
    resolved = destination.resolve()
    if resolved == ROOT or ROOT in resolved.parents or resolved in ROOT.parents:
        raise ValueError('Choose a destination outside this project.')
    if destination.exists():
        raise ValueError(f'{destination} already exists; choose a new folder.')
    if not destination.parent.is_dir():
        raise ValueError(f'The folder {destination.parent} must exist.')
    errors = factory.validate(ROOT, workshop=False)
    if errors:
        raise ValueError('Configuration is invalid; fix it first:\n  ' + '\n  '.join(errors))
    state = site_state.readiness(ROOT)
    problems = [f"{f['path']}: unapproved {f['reason']}" for f in state['open_claims']]
    problems += [f'{path}: To be confirmed' for path in state['placeholders']]
    if problems and not draft:
        raise ValueError('Content is not ready to hand over (use --draft to eject anyway):\n  ' + '\n  '.join(problems))
    env = build.environment()
    with tempfile.TemporaryDirectory(prefix='factory-eject-') as temporary:
        reference = Path(temporary) / 'reference'
        built = subprocess.run([sys.executable, str(ROOT / 'scripts/build.py'), '--destination', str(reference)],
                               cwd=ROOT, env=env, capture_output=True, text=True)
        if built.returncode:
            raise ValueError('This project does not build; fix that first:\n' + (built.stderr or built.stdout).strip()[-1500:])
        destination.mkdir()
        try:
            copy_sources(destination)
            plain = Path(temporary) / 'plain'
            result = subprocess.run(['hugo', '--minify', '--gc', '--destination', str(plain)], cwd=destination,
                                    env=env, capture_output=True, text=True)
            if result.returncode:
                raise ValueError('The ejected copy does not build with plain Hugo:\n' + (result.stdout + result.stderr).strip()[-1500:])
            before, after = tree(reference), tree(plain)
            different = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
            if different:
                raise ValueError('The ejected copy builds a different site; nothing was kept. Differences:\n  ' + '\n  '.join(different[:15]))
            for leftover in ('resources', '.hugo_build.lock'):
                path = destination / leftover
                shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)
        except BaseException:
            shutil.rmtree(destination, ignore_errors=True)
            raise
    return destination, len(after), bool(problems)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('destination', help='A new folder (its parent must exist)')
    parser.add_argument('--draft', action='store_true', help='Eject even with open claims or "To be confirmed" text')
    args = parser.parse_args(argv)
    try:
        destination, files, drafted = eject(args.destination, args.draft)
    except (OSError, ValueError) as error:
        print(f'Cannot eject: {error}', file=sys.stderr)
        return 1
    print(f'Ejected to {destination}: builds with plain Hugo, and its {files} generated files match this project\'s build.')
    if drafted:
        print('Draft: open claims or "To be confirmed" text were left in. Do not hand this over as final.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
