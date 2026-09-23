#!/usr/bin/env python3
"""Check text contrast for the site theme and every palette in data/palettes.json.

  python3 scripts/contrast.py            # data/site.yaml theme + all palettes
  python3 scripts/contrast.py --json

Every text/background pair the templates use must reach WCAG AA (4.5:1) in light and
dark mode. A palette that passes here still needs a visual review; contrast is the part
that can be checked automatically.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
KEYS = ['ink', 'paper', 'mist', 'line', 'accent', 'accent_text', 'link', 'muted',
        'dark_ink', 'dark_paper', 'dark_mist', 'dark_line', 'dark_muted', 'dark_link']
# (text, background) pairs rendered by the templates.
PAIRS = [('ink', 'paper'), ('ink', 'mist'), ('muted', 'paper'), ('muted', 'mist'), ('link', 'paper'), ('link', 'mist'),
         ('accent_text', 'accent'),
         ('dark_ink', 'dark_paper'), ('dark_ink', 'dark_mist'), ('dark_muted', 'dark_paper'), ('dark_muted', 'dark_mist'),
         ('dark_link', 'dark_paper'), ('dark_link', 'dark_mist')]
MINIMUM = 4.5

def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)

def site_theme(root=ROOT):
    block = re.search(r'(?m)^theme:\n((?:[ \t]+.*\n)+)', (root / 'data/site.yaml').read_text()).group(1)
    return dict(re.findall(r'(?m)^[ \t]+(\w+):\s*"(#[0-9a-fA-F]{6})"', block))

def check(theme, label):
    problems = []
    missing = [k for k in KEYS if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(theme.get(k, '')))]
    if missing:
        return [f'{label}: missing or invalid colors: {", ".join(missing)}']
    for text, background in PAIRS:
        value = ratio(theme[text], theme[background])
        if value < MINIMUM:
            problems.append(f'{label}: {text} on {background} is {value:.2f}:1 (needs {MINIMUM}:1)')
    return problems

def palettes(root=ROOT):
    return json.loads((root / 'data/palettes.json').read_text())

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    problems = check(site_theme(), 'data/site.yaml theme')
    for name, palette in palettes().items():
        problems += check(palette['colors'], f'palette {name}')
    if args.json:
        sys.path.insert(0, str(ROOT / 'scripts'))
        from report import emit
        return emit(problems)
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 1
    print(f'Contrast passed: site theme and {len(palettes())} palettes reach {MINIMUM}:1 in light and dark mode.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
