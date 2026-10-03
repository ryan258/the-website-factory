#!/usr/bin/env python3
"""Check that this machine can build and test the factory; print one fix for each problem.

  python3 scripts/doctor.py      # exit 1 only when a required tool is missing or the wrong version

"ok" is good, "warn" limits something optional (browser checks, AI drafting, lint), "FIX" blocks the build.
"""
import importlib.metadata
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(*command):
    try:
        done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    return (done.stdout + done.stderr).strip()

def pin(name):
    path = ROOT / name
    return path.read_text().strip() if path.is_file() else ''

def hugo_ok(text, want):
    """True for the Extended build at the pinned version: "hugo v0.166.0+extended+withdeploy darwin/arm64"."""
    found = re.search(r'v(\d+\.\d+\.\d+)\+extended', text)
    return bool(found) and found.group(1) == want

def check_python():
    ok = sys.version_info >= (3, 11)
    return ('ok' if ok else 'FIX', f'Python {platform.python_version()}', '' if ok else 'install Python 3.11 or newer')

def check_git():
    return ('ok', 'git', '') if shutil.which('git') else ('FIX', 'git', 'install git (the handover report and clean-tree check use it)')

def check_hugo():
    want = pin('.hugo-version')
    if hugo_ok(run('hugo', 'version'), want):
        return 'ok', f'Hugo Extended {want}', ''
    return 'FIX', f'Hugo Extended {want}', f'install the Extended build v{want} from https://github.com/gohugoio/hugo/releases/tag/v{want}'

def check_sass():
    want = pin('.sass-version')
    private = ROOT / '.tools/dart-sass/sass'
    found = str(private) if private.is_file() else shutil.which('sass')
    if found and run(found, '--version').split()[:1] == [want]:
        return 'ok', f'Dart Sass {want}', ''
    return 'FIX', f'Dart Sass {want}', 'run: python3 scripts/setup.py'

def check_node():
    version = run('node', '--version').lstrip('v')
    if version and int(version.split('.')[0]) >= 22:
        return 'ok', f'Node {version}', ''
    return 'warn', 'Node 22 (browser checks, contact tests)', 'install Node 22, the version CI uses'

def check_browser():
    if not (ROOT / 'node_modules').is_dir():
        return 'warn', 'Playwright browser', 'run: npm ci && npx playwright install chromium'
    executable = run('node', '-e', "console.log(require('playwright').chromium.executablePath())")
    if executable and Path(executable).exists():
        return 'ok', 'Playwright browser', ''
    return 'warn', 'Playwright browser', 'run: npx playwright install chromium'

def check_anthropic():
    want = (re.search(r'anthropic==([\d.]+)', pin('requirements-dev.txt')) or [None, ''])[1]
    try:
        have = importlib.metadata.version('anthropic')
    except importlib.metadata.PackageNotFoundError:
        return 'warn', 'anthropic SDK (AI drafting)', 'run: pip install -r requirements-dev.txt (needs Python 3.10+)'
    if have != want:
        return 'warn', f'anthropic {have}', f'requirements-dev.txt pins {want}; older SDKs fail on `fallbacks`. Run: pip install -r requirements-dev.txt'
    return 'ok', f'anthropic {have}', ''

def check_ruff():
    if shutil.which('ruff') or run(sys.executable, '-m', 'ruff', '--version').startswith('ruff'):
        return 'ok', 'ruff (lint)', ''
    return 'warn', 'ruff (npm run lint)', 'run: pip install -r requirements-dev.txt'

def main():
    problems = 0
    for check in (check_python, check_git, check_hugo, check_sass, check_node, check_browser, check_anthropic, check_ruff):
        status, label, fix = check()
        print(f'{status:<5} {label}' + (f' -- {fix}' if fix else ''))
        problems += status == 'FIX'
    vertical = ROOT / 'scripts/vertical_site.py'
    if vertical.is_file():
        import importlib.util
        if importlib.util.find_spec('yaml') is None:
            print('warn  Contractor vertical: install its optional dependency with python3 -m pip install -r requirements-vertical.txt')
    print('Ready to build.' if not problems else f'{problems} problem(s) block the build; fix them first.')
    return 1 if problems else 0

if __name__ == '__main__':
    sys.exit(main())
