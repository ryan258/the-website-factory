#!/usr/bin/env python3
"""Create a source-only client starter without overwriting an existing path."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
from factory import apply_preset, validate

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('assets', 'content', 'data', 'functions', 'layouts', 'static', 'scripts')
FILES = ('hugo.toml', 'wrangler.toml', '.hugo-version', '.sass-version', '.gitignore', 'README.md', 'package.json', 'package-lock.json')

def create(destination, name, preset="agency"):
    if preset not in ("agency", "contractor", "consultant", "local-service"):
        raise ValueError("Unknown business preset.")
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
        shutil.copy2(ROOT / 'docs/cloudflare-setup.md', destination / 'docs/cloudflare-setup.md')
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
        (destination / 'docs/acceptance.md').write_text('# New instance: not yet verified\n\nNo source-project performance or accessibility results apply to this instance. Run the local checks and review all sample content before publication. No deployment or form delivery has been performed.\n')
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    parser.add_argument('--name', required=True)
    parser.add_argument('--preset', choices=['agency','contractor','consultant','local-service'], default='agency')
    args = parser.parse_args()
    try:
        destination = create(args.destination, args.name, args.preset)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Not created: {error}\n')
    print(f'Created {destination}\nEdit data/site.yaml and content/. Read README.md.\nNo Git repository, tool binaries, reports, or generated site was copied. Forms stay disabled; noindex stays on.')

if __name__ == '__main__':
    main()
