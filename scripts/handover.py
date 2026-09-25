#!/usr/bin/env python3
"""Write a plain-language handover report for this site (the master or a client copy).

  python3 scripts/handover.py                         # report on the last build -> reports/handover.md
  python3 scripts/handover.py --build                 # build first, then report
  python3 scripts/handover.py --output docs/acceptance.md

It records what the automated checks found today: configuration, generated output,
pages, search-engine and form settings, placeholders, and claims to confirm. It also
lists what it cannot check, so nobody mistakes it for a full sign-off.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_site  # noqa: E402
import claims  # noqa: E402
import factory  # noqa: E402
import from_plan  # noqa: E402

MANUAL = [
    'Keyboard-only and screen-reader walk-through of every page',
    'Real phone and tablet check, including 200% text size',
    'Every business fact, price, and claim confirmed by the owner in writing',
    'Image rights and alt text reviewed',
    'Live host: HTTPS, security headers, compression, and caching',
    'A real test enquiry sent through the live form and confirmed received (if the form is on)',
]

def setting(pattern, text, default):
    found = re.search(pattern, text, re.M)
    return found.group(1) if found else default

def placeholders(value, path=''):
    if isinstance(value, str):
        return [path] if from_plan.TBC.lower() in value.lower() else []
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in placeholders(v, f'{path}.{k}' if path else k)]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in placeholders(v, f'{path}[{i}]')]
    return []

def report(root=ROOT, output_dir=None):
    output_dir = output_dir or root / 'public'
    config = json.loads((root / 'data/factory.json').read_text())
    preset = json.loads((root / 'data/presets' / f"{config['preset']}.json").read_text())
    hugo = (root / 'hugo.toml').read_text()
    wrangler = (root / 'wrangler.toml').read_text() if (root / 'wrangler.toml').is_file() else ''
    config_errors = factory.validate(root)
    output_errors = check_site.check(output_dir) if output_dir.is_dir() else ['No build output found. Run with --build.']
    found = claims.find(preset)
    open_claims = [f for f in found if not f['approved']]
    gaps = placeholders(preset)
    noindex = setting(r'^\s*noindex\s*=\s*(\w+)', hugo, 'true')
    form = setting(r'^\s*formEnabled\s*=\s*(\w+)', hugo, 'false')
    intake = setting(r'^ENQUIRY_ENABLED\s*=\s*"(\w+)"', wrangler, 'not set')
    base = setting(r"^baseURL\s*=\s*'([^']+)'", hugo, '?')
    manifest_file = output_dir / '.factory-build.json'
    manifest_info = 'not found'
    if manifest_file.is_file():
        import hashlib
        manifest_info = f'`{hashlib.sha256(manifest_file.read_bytes()).hexdigest()[:16]}`'

    git_info = 'unknown'
    try:
        git_res = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=root, capture_output=True, text=True)
        if git_res.returncode == 0:
            dirty_res = subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True)
            dirty = '-dirty' if dirty_res.stdout.strip() else ''
            git_info = f'`{git_res.stdout.strip()}{dirty}`'
    except Exception:
        pass

    ready = not (config_errors or output_errors or open_claims or gaps)
    ok = lambda good: '✅' if good else '❌'
    lines = [
        f'# Handover report: {preset["name"]}', '',
        f'Generated {date.today().isoformat()} by `scripts/handover.py`. Preset `{config["preset"]}`.', '',
        f'- Revision: {git_info}',
        f'- Build manifest: {manifest_info}',
        f'- Python: `{sys.version.split()[0]}`', '',
        f'**Automated status: {"ready for owner review" if ready else "not ready"}.** '
        'This report covers automated checks only; see "Still to check by hand".', '',
        '## Automated checks', '',
        '| Check | Result |', '| --- | --- |',
        f'| Configuration (`scripts/factory.py`) | {ok(not config_errors)} {len(config_errors)} problem(s) |',
        f'| Generated output (`scripts/check_site.py`) | {ok(not output_errors)} {len(output_errors)} problem(s) |',
        f'| Claims to confirm (`scripts/claims.py`) | {ok(not open_claims)} {len(open_claims)} open, {len(found) - len(open_claims)} approved |',
        f'| "{from_plan.TBC}" placeholders | {ok(not gaps)} {len(gaps)} |', '',
    ]
    for title, items in (('Configuration problems', config_errors), ('Output problems', output_errors),
                         ('Claims to confirm', [f'`{f["path"]}`: {f["reason"]} — "{f["match"]}"' for f in open_claims]),
                         ('Placeholders to replace', [f'`{p}`' for p in gaps])):
        if items:
            lines += [f'### {title}', ''] + [f'- {i}' for i in items[:50]] + ([f'- …and {len(items) - 50} more'] if len(items) > 50 else []) + ['']
    lines += ['## Pages', '', '| Page | Title | Sections |', '| --- | --- | --- |']
    lines += [f'| `{"/" if k == "home" else f"/{k}/"}` | {p["title"]} | {", ".join(s["module"] for s in p["sections"])} |'
              for k, p in preset['pages'].items()]
    lines += ['', '## Release settings', '',
              f'- Base URL in `hugo.toml`: `{base}`' + (' (placeholder; set the real domain at release)' if 'example.invalid' in base else ''),
              f'- Search engines: {"blocked (noindex)" if noindex != "false" else "allowed"} by default',
              f'- Contact form: {"on" if form == "true" else "off"} by default; endpoint `ENQUIRY_ENABLED` = `{intake}`',
              '', '## Still to check by hand', ''] + [f'- [ ] {m}' for m in MANUAL] + ['']
    return '\n'.join(lines), ready

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--build', action='store_true', help='Run scripts/build.py first')
    parser.add_argument('--check', '--require-ready', dest='require_ready', action='store_true',
                        help='Exit with non-zero status if not ready')
    parser.add_argument('--output', default='reports/handover.md', help='Where to write (relative to the project)')
    args = parser.parse_args(argv)
    if args.build:
        import build
        res = subprocess.run([sys.executable, str(ROOT / 'scripts/build.py')], cwd=ROOT, env=build.environment(), stdout=sys.stderr)
        if res.returncode != 0:
            print(f'ERROR: Build failed with exit code {res.returncode}. Handover report aborted.', file=sys.stderr)
            return res.returncode
    text, ready = report()
    target = ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    print(f'Wrote {args.output}: {"ready for owner review" if ready else "not ready"}.')
    if args.require_ready and not ready:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
