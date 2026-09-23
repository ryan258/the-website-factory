#!/usr/bin/env python3
"""One command from a client brief to a checked local preview.

  python3 scripts/factory_run.py brief.md ../cedar-studio            # AI draft (paid API call)
  python3 scripts/factory_run.py --plan plan.json ../cedar-studio    # a planner export instead
  python3 scripts/factory_run.py brief.md ../cedar-studio --serve    # then preview on :1313

Steps: draft a plan with Claude (scripts/draft_plan.py) -> compile it into a preset
(scripts/from_plan.py) -> create a separate client copy (scripts/new_site.py) that uses
that preset -> build and check it. The master is never changed. The copy keeps noindex,
a disabled form, and every "To be confirmed" placeholder; docs/plan-review.md in the
copy lists what a person must confirm before anything is published.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build  # noqa: E402
import claims  # noqa: E402
import factory  # noqa: E402
import from_plan  # noqa: E402
import new_site  # noqa: E402

# The copy starts from this preset, then its pages are replaced by the compiled plan.
BASE = 'consultant'

def placeholders(value, path='preset'):
    if isinstance(value, str):
        if from_plan.TBC in value:
            yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from placeholders(item, f'{path}.{key}')
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from placeholders(item, f'{path}[{i}]')

def review(preset, plan_file):
    lines = [f'# Plan review: {preset["name"]}', '',
             f'Drafted from `{plan_file}`. Nothing here is approved. Confirm every fact with the client.', '',
             f'## Placeholders to replace ("{from_plan.TBC}")', '']
    gaps = list(placeholders(preset))
    lines += [f'- `{path}`: {text}' for path, text in gaps] or ['- None.']
    lines += ['', '## Claims to confirm (scripts/claims.py)', '']
    found = claims.find(preset)
    lines += [f'- `{f["path"]}`: {f["reason"]} — "{f["match"]}"' for f in found] or ['- None found.']
    lines += ['', 'Edit `data/presets/*.json`, then run `python3 scripts/build.py` and `python3 scripts/claims.py`.', '']
    return '\n'.join(lines), len(gaps), len(found)

def run(plan, destination, name=None, plan_file='plan.json'):
    """Create and build a client copy from a planner export. Returns (copy path, build exit code)."""
    registry = json.loads((ROOT / 'data/modules.json').read_text())
    slug, preset = from_plan.convert_plan_to_preset(plan, registry)
    name = name or preset['name']
    preset['name'] = name
    errors = factory.validate(ROOT, extra_presets={slug: preset})
    if errors:
        raise ValueError('The compiled preset is not valid:\n  ' + '\n  '.join(errors))
    dest = new_site.create(destination, name, BASE)
    (dest / 'data/presets' / f'{slug}.json').write_text(json.dumps(preset, indent=2, ensure_ascii=False) + '\n')
    factory.apply_preset(dest, slug, name)
    errors = factory.validate(dest)
    if errors:
        raise ValueError('The new copy did not validate:\n  ' + '\n  '.join(errors))
    (dest / 'docs/plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')
    text, gaps, found = review(preset, plan_file)
    (dest / 'docs/plan-review.md').write_text(text)
    # The copy has no .tools of its own yet; build with the master's pinned Hugo and Sass.
    # Build progress goes to stderr, so a caller that owns stdout (the MCP server) stays clean.
    built = subprocess.run([sys.executable, str(dest / 'scripts/build.py')], cwd=dest, env=build.environment(),
                           stdout=sys.stderr)
    print(f'{dest}: {len(preset["pages"])} pages, {gaps} placeholder(s), {found} claim(s) to confirm. '
          'See docs/plan-review.md in the copy.', file=sys.stderr)
    return dest, built.returncode

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('brief', nargs='?', help='Client brief (text or Markdown); drafted with Claude')
    parser.add_argument('destination', help='New folder for the client copy (must not exist)')
    parser.add_argument('--plan', help='Use this planner export instead of drafting from a brief')
    parser.add_argument('--name', help='Business name (default: the plan\'s name)')
    parser.add_argument('--serve', action='store_true', help='Serve the checked copy on http://127.0.0.1:1313/')
    args = parser.parse_args(argv)
    if bool(args.brief) == bool(args.plan):
        parser.error('Give either a brief or --plan, not both.')
    if args.plan:
        plan_file = Path(args.plan).name
        plan = json.loads(Path(args.plan).read_text())
    else:
        import draft_plan
        plan_file = Path(args.brief).name
        plan = draft_plan.draft(Path(args.brief).read_text(), source=plan_file)
    try:
        dest, code = run(plan, args.destination, args.name, plan_file)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    if code == 0 and args.serve:
        return subprocess.call([sys.executable, str(dest / 'scripts/build.py'), '--serve'], cwd=dest, env=build.environment())
    return code

if __name__ == '__main__':
    sys.exit(main())
