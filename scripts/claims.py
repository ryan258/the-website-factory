#!/usr/bin/env python3
"""Flag copy that states a fact someone should be able to back up.

  python3 scripts/claims.py                 # the selected preset; report only
  python3 scripts/claims.py --preset agency # another preset
  python3 scripts/claims.py --strict        # exit 1 while any claim is unapproved
  python3 scripts/claims.py --json

Looks at the text a preset actually renders (sections used by its pages) for prices,
percentages, counts ("200 clients", "10 years"), ratings, testimonials, and absolute
words ("best", "guaranteed", "award-winning"). It cannot tell true from false; it points
at what a person must confirm.

Approve a claim by adding its exact text, or a phrase inside it, to the preset's
"approved_claims" list once the business has confirmed it. Client copies start with no
approvals (scripts/factory.py apply_preset drops the list).
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RULES = [
    ('PRICE', r'[$€£]\s?\d[\d,.]*\s?(?:k\b)?', 'a price or amount'),
    ('PERCENT', r'\b\d+(?:\.\d+)?\s?%', 'a percentage'),
    ('COUNT', r'\b\d[\d,]*\+?\s+(?:happy\s+)?(?:clients|customers|projects|years|sites|websites|businesses|reviews|'
              r'patients|members|families|students|donors|volunteers)\b', 'a count of clients, years, or results'),
    ('RATING', r'\b\d(?:\.\d)?\s?(?:stars?|/\s?5|out of 5)\b', 'a rating'),
    ('ABSOLUTE', r'(?i)\b(?:best|#1|number one|leading|top[- ]rated|award[- ]winning|world[- ]class|unmatched|'
                 r'unbeatable|guarantee[sd]?|proven|certified|accredited|licensed|insured|fastest|cheapest|lowest price)\b',
     'an absolute or credential claim'),
]
# Every testimonial is a claim that a real person said it.
QUOTE_MODULES = {'testimonials'}

def rendered_strings(preset):
    """(json path, module, text) for every string the preset's pages render."""
    used = {}
    for page, definition in preset.get('pages', {}).items():
        for section in definition.get('sections', []):
            used.setdefault(section.get('content'), section.get('module'))
    def walk(value, path, module):
        if isinstance(value, str):
            yield path, module, value
        elif isinstance(value, dict):
            for key, item in value.items():
                if key not in ('url', 'image', 'variant', 'group', 'art'):
                    yield from walk(item, f'{path}.{key}', module)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                yield from walk(item, f'{path}[{i}]', module)
    for key, module in used.items():
        yield from walk(preset.get('sections', {}).get(key), f'sections.{key}', module)
    for page, definition in preset.get('pages', {}).items():
        for field in ('title', 'description'):
            if isinstance(definition.get(field), str):
                yield f'pages.{page}.{field}', None, definition[field]

def denied(sentence, start):
    """A question asks rather than claims, and 'not a guarantee' denies one: neither needs proof."""
    if sentence.rstrip().endswith('?'):
        return True
    return bool(re.search(r"(?i)\b(?:not|no|never|without|don't|doesn't|cannot|can't|isn't)\b(?:\W+\w+){0,3}\W*$",
                          sentence[:start]))

def find(preset):
    approved = [a for a in preset.get('approved_claims', []) if isinstance(a, str) and a.strip()]
    findings = []
    for path, module, text in rendered_strings(preset):
        hits = [(code, m.group(0), why) for sentence in re.split(r'(?<=[.!?])\s+', text)
                for code, pattern, why in RULES for m in re.finditer(pattern, sentence)
                if not denied(sentence, m.start())]
        if module in QUOTE_MODULES and re.search(r'\.text$', path):
            hits.append(('TESTIMONIAL', text[:60], 'a quote attributed to a real person'))
        for code, match, why in hits:
            findings.append(dict(code=f'CLAIM_{code}', path=path, match=match.strip(), text=text, reason=why,
                                 approved=any(a in text or text in a for a in approved)))
    return findings

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--preset', help='Preset slug (default: the one selected in data/factory.json)')
    parser.add_argument('--strict', action='store_true', help='Exit 1 while any claim is unapproved')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    slug = args.preset or json.loads((ROOT / 'data/factory.json').read_text())['preset']
    path = ROOT / 'data/presets' / f'{slug}.json'
    if not path.is_file():
        parser.error(f'No preset {slug}.')
    findings = find(json.loads(path.read_text()))
    open_items = [f for f in findings if not f['approved']]
    if args.json:
        json.dump(dict(ok=not open_items, preset=slug, findings=findings), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')
    else:
        for f in findings:
            mark = 'approved' if f['approved'] else 'CONFIRM '
            print(f'{mark}  {f["path"]}: {f["reason"]} — "{f["match"]}"')
        print(f'{slug}: {len(open_items)} claim(s) to confirm, {len(findings) - len(open_items)} approved. '
              f'Approve confirmed ones in "approved_claims" in {path.relative_to(ROOT)}.', file=sys.stderr)
    return 1 if args.strict and open_items else 0

if __name__ == '__main__':
    sys.exit(main())
