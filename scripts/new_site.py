#!/usr/bin/env python3
"""Create a source-only client starter without overwriting an existing path."""
import argparse
import json
from pathlib import Path
import re
import shutil
from factory import apply_preset, validate

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('assets', 'content', 'data', 'functions', 'layouts', 'static', 'scripts')
FILES = ('hugo.toml', '.hugo-version', '.sass-version', '.gitignore', 'README.md', 'package.json', 'package-lock.json')

def available_presets():
    """Every preset in data/presets, including ones compiled by scripts/from_plan.py."""
    return sorted(p.stem for p in (ROOT / 'data/presets').glob('*.json'))

def project_slug(name):
    """A Cloudflare-safe project name derived from the client name."""
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:54]
    return slug or 'client-site'

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
python3 scripts/setup.py     # fetches the pinned Dart Sass
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
form works. Agree who monitors enquiries, and how often, before launch.

## 4. Publishing decisions that remain open

- `noindex` stays on and `baseURL` stays at `example.invalid` until the owner decides
  otherwise (`hugo.toml`).
- Sample content, prices, claims, and contact details must be replaced with confirmed
  client facts.
- Performance and accessibility results from the source project do not transfer. Re-run
  the checks against this instance.
""")


def create(destination, name, preset="agency"):
    if preset not in available_presets():
        raise ValueError(f"Unknown business preset. Choose one of: {', '.join(available_presets())}.")
    errors = validate(ROOT)
    if errors:
        raise ValueError("Invalid master: " + "; ".join(errors))
    destination = Path(destination).expanduser().absolute()
    resolved = destination.resolve()
    if not name.strip() or len(name) > 60 or any(ord(c) < 32 for c in name):
        raise ValueError('Name must be 1–60 characters without control characters.')
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError('Choose a destination outside the source project.')
    if not destination.parent.is_dir():
        raise ValueError('Destination parent must already exist.')
    for folder in FOLDERS:
        for path in (ROOT / folder).rglob('*'):
            if path.is_symlink():
                raise ValueError(f'Source symlinks are not copied: {path.relative_to(ROOT)}')
    for filename in FILES:
        if (ROOT / filename).is_symlink():
            raise ValueError(f'Source symlinks are not copied: {filename}')
    destination.mkdir()  # Exclusive creation: existing files/directories/symlinks fail.
    try:
        for folder in FOLDERS:
            shutil.copytree(ROOT / folder, destination / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        for filename in FILES:
            shutil.copy2(ROOT / filename, destination / filename)
        (destination / 'docs').mkdir()
        shutil.copy2(ROOT / 'docs/starter-guide.md', destination / 'docs/starter-guide.md')
        shutil.copy2(ROOT / 'docs/factory-guide.md', destination / 'docs/factory-guide.md')
        shutil.copy2(ROOT / 'docs/agency-workflow.md', destination / 'docs/agency-workflow.md')
        shutil.copy2(ROOT / 'docs/component-library.md', destination / 'docs/component-library.md')
        write_deployment(destination, name)
        config = destination / 'data/site.yaml'
        text = config.read_text()
        for key, value in [('name', name), ('wordmark', name), ('email', 'hello@example.invalid')]:
            text, count = re.subn(r'^' + key + r':.*$', lambda _: key + ': ' + json.dumps(value, ensure_ascii=False), text, count=1, flags=re.M)
            if count != 1:
                raise ValueError(f'Expected exactly one top-level {key} in data/site.yaml.')
        config.write_text(text)
        apply_preset(destination, preset, name)
        readme = destination / 'README.md'
        readme.write_text(f'> Client draft: {name}. Preset: `{preset}`. This copy excludes the master workshop and other presets. The factory reference below documents the shared system; see `docs/factory-guide.md` for editing this copy.\n\n' + readme.read_text())
        # Each new instance starts private and disabled, irrespective of source settings.
        conf = destination / 'hugo.toml'
        text = conf.read_text()
        text = re.sub(r'^baseURL\s*=.*$', "baseURL = 'https://example.invalid/'", text, flags=re.M)
        text = re.sub(r'^\s*formEnabled\s*=.*$', '  formEnabled = false', text, flags=re.M)
        text = re.sub(r'^\s*noindex\s*=.*$', '  noindex = true', text, flags=re.M)
        conf.write_text(text)
        (destination / 'docs/acceptance.md').write_text('# New instance: not yet verified\n\nNo source-project performance or accessibility results apply to this instance. Run the local checks and review all sample content before publication. No deployment or form delivery has been performed.\n\nWhen the site is ready for review, replace this file with a fresh report:\n\n    python3 scripts/handover.py --build --output docs/acceptance.md\n')
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    parser.add_argument('--name', required=True)
    parser.add_argument('--preset', choices=available_presets(), default='agency')
    args = parser.parse_args()
    try:
        destination = create(args.destination, args.name, args.preset)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Not created: {error}\n')
    print(f'Created {destination}\nEdit data/site.yaml and content/. Read README.md.\nNo Git repository, tool binaries, reports, or generated site was copied. Forms stay disabled; noindex stays on.\nNo hosting resources were copied: wrangler.toml is unconfigured and /api/contact refuses submissions until this client declares its own. See docs/cloudflare-setup.md.')

if __name__ == '__main__':
    main()
