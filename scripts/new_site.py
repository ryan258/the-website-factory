#!/usr/bin/env python3
"""Create a source-only client starter without overwriting an existing path."""
import argparse
import json
from pathlib import Path
import re
import shutil
from factory import apply_fonts, apply_palette, apply_preset, validate
from scaffold_core import copy_sources

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('assets', 'content', 'data', 'functions', 'layouts', 'static', 'scripts', 'schemas')
FILES = ('hugo.toml', '.hugo-version', '.sass-version', '.gitignore', 'README.md', 'package.json', 'package-lock.json',
         '.mcp.json', 'requirements-dev.txt', 'ruff.toml', 'wf')
# These test or gate the master itself (every preset, the scaffold, the eval fixtures, a git
# checkout), so they cannot pass in a one-preset client copy. The copy's npm test runs checks that fit a client site.
MASTER_ONLY_TESTS = ('test_factory.py', 'test_starter.py', 'test_from_plan.py', 'test_schemas.py', 'test_claims.py',
                     'test_ai.py', 'test_mcp.py', 'test_evals.py', 'test_handover.py', 'test_library.py', 'test_enquiries.py',
                     'test_links.py', 'test_doctor.py', 'test_setup.py', 'test_smoke.py', 'test_care.py', 'test_plan_fidelity.py', 'test_scaffold_core.py',
                     'test_review_fixes.py', 'test_three_layouts.py', 'test_component_expansion.py', 'check_planner_fidelity.cjs',
                     'check_workshop.cjs', 'check_components.cjs', 'check_workflow.cjs', 'verify.py', 'verify_review.py')
CLIENT_TEST = ('python3 scripts/factory.py && python3 scripts/check_site.py && python3 scripts/claims.py --strict '
               '&& python3 scripts/contrast.py && node scripts/test_contact_endpoint.mjs')

def client_package(destination):
    """Point npm scripts at checks that exist and make sense in a client copy."""
    package = destination / 'package.json'
    data = json.loads(package.read_text())
    scripts = data.get('scripts', {})
    for name, command in list(scripts.items()):
        if any(test in command for test in MASTER_ONLY_TESTS) or 'eval_plans.py' in command:
            del scripts[name]
    scripts['test'] = CLIENT_TEST
    package.write_text(json.dumps(data, indent=2) + '\n')

def available_presets():
    """Every preset in data/presets, including ones compiled by scripts/from_plan.py."""
    return sorted(p.stem for p in (ROOT / 'data/presets').glob('*.json'))

def project_slug(name):
    """A Cloudflare-safe project name derived from the client name."""
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:54]
    return slug or 'client-site'

CLIENT_CI = """name: Check

# Builds this site and runs its checks on every push. It deploys nothing and uses no secrets
# beyond the built-in read-only token. Publishing stays a separate, owner-controlled step.
on:
  push:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  check:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    steps:
      - uses: {checkout}
      - uses: {python}
        with:
          python-version: '3.11'
      - uses: {node}
        with:
          node-version: '22'
      - name: Install pinned Hugo and Dart Sass
        env:
          GITHUB_TOKEN: ${{{{ github.token }}}}
        run: python3 scripts/setup.py
      - name: Build and check the site
        run: python3 scripts/build.py
      - name: Client checks
        run: npm test
"""

def write_ci(destination):
    """A check-only workflow for the client's own repository, pinned to the master's exact action commits."""
    pinned = {}
    # The master's deploy workflows, or in a client copy making another copy, its own check.yml.
    for line in ''.join(f.read_text() for f in sorted((ROOT / '.github/workflows').glob('*.yml'))).splitlines():
        found = re.search(r'uses: ([\w.-]+/[\w.-]+)@([0-9a-f]{40} # \S+)', line)
        if found:
            pinned[found.group(1)] = f'{found.group(1)}@{found.group(2)}'
    path = destination / '.github/workflows/check.yml'
    path.parent.mkdir(parents=True)
    path.write_text(CLIENT_CI.format(checkout=pinned['actions/checkout'], python=pinned['actions/setup-python'],
                                     node=pinned['actions/setup-node']))

def write_deployment(destination, name):
    """Write an unconfigured Wrangler file and a client-specific setup guide.

    The master's wrangler.toml names live resources (an ENQUIRY KV id, a Pages project) and
    its setup guide names a live domain and mailbox. Neither is copied: a new instance
    must create and declare its own, so it can never write into the master's namespace.
    """
    master = (ROOT / 'wrangler.toml').read_text()
    compatibility = re.search(r'(?m)^compatibility_date\s*=\s*"([\d-]+)"', master)
    if not compatibility:
        raise ValueError('Master wrangler.toml has no compatibility_date to carry over.')
    slug = project_slug(name)
    (destination / 'wrangler.toml').write_text(f"""# Deployment configuration for {name}. Nothing is configured yet, and no resource from
# the source project is carried over: no bucket, no namespace id, no notification address.
#
# /api/contact returns 503 until BOTH of the following are true for this deployment:
#   1. it declares this client's own ENQUIRY namespace (below), and
#   2. its environment sets ENQUIRY_ENABLED = "true".
# Enabling the rendered form in hugo.toml does not open the endpoint on its own.
# See docs/cloudflare-setup.md.

name = "{slug}"
pages_build_output_dir = "public"
compatibility_date = "{compatibility.group(1)}"

# Step 1 — create this client's own store:  npx wrangler kv namespace create ENQUIRY
# Step 2 — paste its id here and uncomment all three lines.
# [[kv_namespaces]]
# binding = "ENQUIRY"
# id = ""

# Step 3 — open intake for this deployment, once the namespace above is this client's.
# [vars]
# ENQUIRY_ENABLED = "true"
""")
    (destination / 'docs/cloudflare-setup.md').write_text(f"""# Deploying {name}

This instance has no hosting account, domain, resources, or enquiry destination of its
own yet. Nothing from the source project applies to it. Work through the steps below
with the client's own Cloudflare account.

## 1. Build locally

```sh
python3 scripts/setup.py     # fetches the pinned Hugo and Dart Sass
python3 scripts/build.py     # builds public/ and runs the generated-output checks
```

## 2. Create this client's Pages project

```sh
npx wrangler pages project create {slug} --production-branch main
npx wrangler pages deploy public --project-name {slug}
```

Review the `.pages.dev` preview before any custom domain is attached. Adding a domain is
the client's decision, not a step this guide assumes.

## 3. Decide whether this site accepts enquiries

The contact form is inert until all three are done, in this order:

1. `npx wrangler kv namespace create ENQUIRY` — a namespace owned by this client.
2. Put its id in `wrangler.toml` and uncomment the `[[kv_namespaces]]` block.
3. Uncomment `[vars] ENQUIRY_ENABLED = "true"` there, or set that variable on the Pages
   project. Without it the endpoint refuses every submission, deliberately.

Then build with the form rendered: `HUGO_PARAMS_FORMENABLED=true python3 scripts/build.py`,
and confirm receipt end to end (`scripts/check_contact.sh`, or a real submission read back
with `npx wrangler kv key list --binding ENQUIRY --remote`) before telling the client the
form works. Set a secret salt for the rate limiter (`npx wrangler pages secret put RATE_LIMIT_SALT --project-name {slug}`, any long random
string), or the stored IP hashes can be reversed. Agree who monitors enquiries, and how often, before launch.

## 4. Publishing decisions that remain open

- `noindex` stays on and `baseURL` stays at `example.invalid` until the owner decides
  otherwise (`hugo.toml`).
- Sample content, prices, claims, and contact details must be replaced with confirmed
  client facts.
- Performance and accessibility results from the source project do not transfer. Re-run
  the checks against this instance.
""")


TITLE_LIMIT = 60  # scripts/check_site.py fails a page title of 60 characters or more

def page_titles(root, profile):
    """Every title a copy built from this profile can show, before its " — name" ending."""
    titles = ['404 Page not found'] + [page.get('seo_title') or page['title'] for page in profile['pages'].values()]
    for key in profile['pages']:
        if key == 'home':
            continue
        for file in (Path(root) / 'content' / key).glob('*.md'):
            if file.name != '_index.md':  # section pages take their title from the preset
                found = re.search(r'(?m)^title:\s*"?(.*?)"?\s*$', file.read_text())
                if found:
                    titles.append(found.group(1))
    return titles

def long_title(root, profile, name):
    """The longest page title for this name, or None when every title fits in search results."""
    title = f'{max(page_titles(root, profile), key=len)} — {name}'
    return title if len(title) >= TITLE_LIMIT else None

def create(destination, name, preset="agency", palette=None, fonts=None, *, profile=None, short_name=None):
    """Apply the final profile once, before pruning any source pages, images, or fonts."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', preset):
        raise ValueError('Preset identifier must contain lowercase letters, digits, and hyphens.')
    if profile is None and preset not in available_presets():
        raise ValueError(f"Unknown business preset. Choose one of: {', '.join(available_presets())}.")
    errors = validate(ROOT, extra_presets={preset: profile} if profile is not None else None)
    if errors:
        raise ValueError("Invalid master: " + "; ".join(errors))
    destination = Path(destination).expanduser().absolute()
    resolved = destination.resolve()
    if not name.strip() or len(name) > 60 or any(ord(c) < 32 for c in name):
        raise ValueError('Name must be 1–60 characters without control characters.')
    short_name = (short_name or '').strip() or None
    if short_name and (len(short_name) > 30 or any(ord(c) < 32 for c in short_name)):
        raise ValueError('Short name must be 1–30 characters without control characters.')

    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError('Choose a destination outside the source project.')
    if not destination.parent.is_dir():
        raise ValueError('Destination parent must already exist.')
    copy_sources(ROOT, destination, FOLDERS, FILES)
    try:
        (destination / 'docs').mkdir()
        for test in MASTER_ONLY_TESTS:
            (destination / 'scripts' / test).unlink(missing_ok=True)
        # Specialist masters are selected only from the central checkout.
        (destination / 'scripts/vertical_site.py').unlink(missing_ok=True)
        shutil.rmtree(destination / 'scripts/fixtures', ignore_errors=True)  # recorded planner exports for the master's tests
        client_package(destination)
        shutil.copy2(ROOT / 'docs/starter-guide.md', destination / 'docs/starter-guide.md')
        shutil.copy2(ROOT / 'docs/factory-guide.md', destination / 'docs/factory-guide.md')
        shutil.copy2(ROOT / 'docs/agency-workflow.md', destination / 'docs/agency-workflow.md')
        shutil.copy2(ROOT / 'docs/component-library.md', destination / 'docs/component-library.md')
        write_deployment(destination, name)
        write_ci(destination)
        config = destination / 'data/site.yaml'
        text = config.read_text()
        for key, value in [('name', name), ('wordmark', name), ('email', 'hello@example.invalid')]:
            text, count = re.subn(r'^' + key + r':.*$', lambda _: key + ': ' + json.dumps(value, ensure_ascii=False), text, count=1, flags=re.M)
            if count != 1:
                raise ValueError(f'Expected exactly one top-level {key} in data/site.yaml.')
        text = re.sub(r'^short_name:.*\n', '', text, flags=re.M)
        if short_name:
            text = re.sub(r'^(name:.*\n)', lambda m: m.group(1) + 'short_name: ' + json.dumps(short_name, ensure_ascii=False) + '\n',
                          text, count=1, flags=re.M)
        config.write_text(text)
        profile_defaults = profile if profile is not None else json.loads((ROOT / 'data/presets' / f'{preset}.json').read_text())
        if profile is not None:
            (destination / 'data/presets' / f'{preset}.json').write_text(json.dumps(profile, indent=2, ensure_ascii=False) + '\n')
        apply_preset(destination, preset, name)
        # Checked on the pruned copy, so only pages it actually has count.
        too_long = long_title(destination, profile_defaults, short_name or name)
        if too_long:
            raise ValueError(f'Page titles would be too long for search results ({len(too_long)} characters: "{too_long}"). '
                             'Give a short name for titles (--short-name, or the guided question); the full name stays everywhere else.')
        (destination / 'data/content-review.json').unlink(missing_ok=True)
        selected_palette = palette or profile_defaults.get('palette')
        # 'modern' is the master's own font block; applying it drops the four unused font families.
        selected_fonts = fonts or profile_defaults.get('font_pairing') or 'modern'
        if selected_palette:
            apply_palette(destination, selected_palette)
        if selected_fonts:
            apply_fonts(destination, selected_fonts)
        from client_docs import write
        write(destination, name, preset)
        # Each new instance starts private and disabled, irrespective of source settings.
        conf = destination / 'hugo.toml'
        text = conf.read_text()
        text = re.sub(r'^baseURL\s*=.*$', "baseURL = 'https://example.invalid/'", text, flags=re.M)
        text = re.sub(r'^\s*formEnabled\s*=.*$', '  formEnabled = false', text, flags=re.M)
        text = re.sub(r'^\s*noindex\s*=.*$', '  noindex = true', text, flags=re.M)
        text = re.sub(r"^\s*formAction\s*=.*$", "  formAction = ''", text, flags=re.M)
        conf.write_text(text)
        (destination / 'docs/acceptance.md').write_text('# New instance: not yet verified\n\nNo source-project performance or accessibility results apply to this instance. Run the local checks and review all sample content before publication. No deployment or form delivery has been performed.\n\nWhen the site is ready for review, replace this file with a fresh report:\n\n    python3 scripts/handover.py --build --output docs/acceptance.md\n')
        final_errors = validate(destination)
        if final_errors:
            raise ValueError('Client configuration is invalid: ' + '; '.join(final_errors))
    except BaseException:
        shutil.rmtree(destination)
        raise
    return destination

NEXT_STEPS = ('Edit data/site.yaml and content/. Read README.md.\nNo Git repository, tool binaries, reports, or generated site '
              'was copied. Forms stay disabled; noindex stays on.\nNo hosting resources were copied: wrangler.toml is unconfigured '
              'and /api/contact refuses submissions until this client declares its own. See docs/cloudflare-setup.md.')

def choose(ask, title, options, default=0):
    """Ask for one of options [(value, label, description)] by letter (or number, or name). Returns the value."""
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    print(f'\n{title}')
    for i, (value, label, description) in enumerate(options):
        mark = ' (default)' if i == default else ''
        print(f'  {letters[i]}. {label}{mark}' + (f' — {description}' if description else ''))
    for _ in range(5):
        answer = ask(f'Type a letter and press Enter [{letters[default]}]: ').strip()
        if not answer:
            return options[default][0]
        for i, (value, label, _) in enumerate(options):
            if answer.upper() == letters[i] or answer == str(i + 1) or answer.lower() in (str(value).lower(), label.lower()):
                return value
        print(f'  "{answer}" is not one of the letters shown. Please try again.')
    raise ValueError('No choice made.')

def choose_pages(ask, preset, profile, step):
    """Which pages to keep, in menu order. Returns the profile itself when every page is kept as it is."""
    pages = list(profile['pages'])
    print(f'\n{step} — Pages (each page is one menu item, in this order)')
    for key in pages:
        print(f'  {key}: {profile["pages"][key].get("title", key)}')
    for _ in range(5):
        answer = ask(f'Type the pages to keep, in menu order, or press Enter to keep all [{" ".join(pages)}]: ')
        chosen = answer.replace(',', ' ').lower().split()
        if not chosen or chosen == pages:
            return profile
        if any(page not in pages for page in chosen) or len(set(chosen)) != len(chosen):
            print(f'  Use each page name once, from: {" ".join(pages)}.')
            continue
        candidate = {**profile, 'pages': {key: profile['pages'][key] for key in chosen}}
        errors = validate(ROOT, extra_presets={preset: candidate})
        if not errors:
            return candidate
        print('  Those pages do not work together yet:')
        for error in errors[:5]:
            print(f'    {error}')
    raise ValueError('No page selection made.')

def guided(ask=input):
    """Ask one question at a time; nothing is created until the summary is confirmed."""
    print('Guided setup: a new client copy, one question at a time. Press Enter to accept a default.')
    print('\nStep 1 of 6 — Business name')
    name = ''
    for _ in range(5):
        name = ask('Type the business name: ').strip()
        if name and '\n' not in name:
            break
        print('  Please type a name.')
    if not name:
        raise ValueError('No business name given.')
    suggested = ROOT.parent / project_slug(name)
    print('\nStep 2 of 6 — Where to put the copy (a folder that does not exist yet)')
    destination = ask(f'Folder [{suggested}]: ').strip() or str(suggested)
    presets = [(slug, slug, json.loads((ROOT / 'data/presets' / f'{slug}.json').read_text()).get('label', ''))
               for slug in available_presets()]
    preset = choose(ask, 'Step 3 of 6 — Starting preset (pages and sections you can change later)', presets,
                    next((i for i, p in enumerate(presets) if p[0] == 'agency'), 0))
    profile_defaults = json.loads((ROOT / 'data/presets' / f'{preset}.json').read_text())
    profile = choose_pages(ask, preset, profile_defaults, 'Step 4 of 6')
    short_name = None
    if long_title(ROOT, profile, name):
        print(f'\nShort name for page titles\n  "{long_title(ROOT, profile, name)}" may be cut off in search results.'
              '\n  Titles can use a shorter name; the header, footer and search data keep the full name.')
        for _ in range(5):
            short_name = ask('Short name for titles (Enter to keep the full name): ').strip() or None
            if not short_name or (len(short_name) <= 30 and not long_title(ROOT, profile, short_name)):
                break
            print('  Still too long. Try 30 characters or fewer.')
    palettes = json.loads((ROOT / 'data/palettes.json').read_text())
    palette = choose(ask, 'Step 5 of 6 — Colors (every palette passes contrast checks)',
                     [(None, 'Preset colors', f'use {profile_defaults.get("palette")}' if profile_defaults.get('palette') else 'keep the preset accent color')]
                     + [(key, key, p['use']) for key, p in palettes.items()])
    fonts = json.loads((ROOT / 'data/fonts.json').read_text())
    pairing = choose(ask, 'Step 6 of 6 — Fonts (self-hosted, open-licensed)',
                     [(None, 'Preset font pairing', f'use {profile_defaults.get("font_pairing", "modern")}')]
                     + [(key, key, f['use']) for key, f in fonts.items()])
    print(f'\nSummary\n  Name:    {name}\n  Folder:  {destination}\n  Preset:  {preset}\n'
          f'  Pages:   {" ".join(profile["pages"])}\n'
          + (f'  Titles:  {short_name}\n' if short_name else '') +
          f'  Colors:  {palette or profile_defaults.get("palette", "preset accent")}\n'
          f'  Fonts:   {pairing or profile_defaults.get("font_pairing", "modern")}')
    if choose(ask, 'Create this copy?', [(True, 'Yes, create it', ''), (False, 'No, cancel', '')]) is not True:
        print('Cancelled. Nothing was created.')
        return None
    return create(destination, name, preset, palette, pairing, profile=None if profile is profile_defaults else profile,
                  short_name=short_name)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?')
    parser.add_argument('--name')
    parser.add_argument('--preset', choices=available_presets(), default='agency')
    parser.add_argument('--palette', choices=sorted(json.loads((ROOT / 'data/palettes.json').read_text())),
                        help='Color palette from data/palettes.json (contrast-checked); default: the preset accent')
    parser.add_argument('--fonts', choices=sorted(json.loads((ROOT / 'data/fonts.json').read_text())),
                        help='Font pairing from data/fonts.json (self-hosted, open-licensed); default: Inter')
    parser.add_argument('--short-name', help='Shorter name for page titles when the full name makes them too long (30 characters at most)')
    parser.add_argument('--guided', action='store_true', help='Answer a few lettered questions instead of passing options')
    args = parser.parse_args()
    if args.guided:
        try:
            destination = guided()
        except (EOFError, KeyboardInterrupt):
            parser.exit(1, '\nCancelled. Nothing was created.\n')
        except (OSError, ValueError) as error:
            parser.exit(1, f'Not created: {error}\n')
        if destination:
            print(f'\nCreated {destination}\n{NEXT_STEPS}')
        return
    if not args.destination or not args.name:
        parser.error('give a destination and --name, or use --guided')
    try:
        destination = create(args.destination, args.name, args.preset, args.palette, args.fonts, short_name=args.short_name)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Not created: {error}\n')
    print(f'Created {destination}\n{NEXT_STEPS}')

if __name__ == '__main__':
    main()
