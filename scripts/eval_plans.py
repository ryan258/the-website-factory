#!/usr/bin/env python3
"""Score AI-drafted page plans against written expectations.

  python3 scripts/eval_plans.py                     # score saved drafts in evals/recorded/ (free)
  python3 scripts/eval_plans.py --live              # draft each brief with Claude now (paid)
  python3 scripts/eval_plans.py --live --record     # ...and save the drafts to evals/recorded/
  python3 scripts/eval_plans.py --min-score 1.0     # exit 1 below this average score

Each evals/briefs/<name>.md has a <name>.expect.json. Grading is plain code, no model:
  schema        the draft matches schemas/plan.schema.json
  compiles      scripts/from_plan.py turns it into a preset that passes scripts/factory.py
  pages         page count is within min_pages..max_pages
  modules       every required_modules entry is used
  mentions      every must_mention phrase appears (facts from the brief were used)
  no_invention  no must_not_mention phrase appears (invented prices, credentials, stats)
  unknowns      every must_mark_unknown topic is marked "To be confirmed" or listed as unknown
  claims        scripts/claims.py finds nothing to confirm in the compiled preset
A live run costs one API call per brief. Results are written to reports/evals/.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import claims  # noqa: E402
import factory  # noqa: E402
import from_plan  # noqa: E402
import schemas  # noqa: E402

BRIEFS = ROOT / 'evals/briefs'
RECORDED = ROOT / 'evals/recorded'

def all_text(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in all_text(v)]
    if isinstance(value, list):
        return [t for v in value for t in all_text(v)]
    return []

def grade(plan, expect, registry):
    """Return {check: (passed, detail)} for one draft."""
    import draft_plan
    results = {}
    problems = schemas.validate(plan, schemas.plan_schema(registry))
    results['schema'] = (not problems, '; '.join(problems[:3]) or 'ok')
    if problems:
        return results
    texts = all_text(plan)
    lower = ' '.join(texts).lower()
    try:
        slug, preset = from_plan.convert_plan_to_preset(draft_plan.to_planner(plan, registry), registry)
        errors = factory.validate(ROOT, extra_presets={slug: preset})
        errors = [e for e in errors if e.startswith(slug)]
    except ValueError as error:
        preset, errors = None, [str(error)]
    results['compiles'] = (not errors, '; '.join(errors[:3]) or 'ok')
    pages = len(plan['pages'])
    results['pages'] = (expect['min_pages'] <= pages <= expect['max_pages'], f'{pages} pages')
    used = {s['kind'] for p in plan['pages'] for s in p['sections']}
    missing = [m for m in expect['required_modules'] if m not in used]
    results['modules'] = (not missing, 'missing ' + ', '.join(missing) if missing else 'ok')
    absent = [m for m in expect['must_mention'] if m.lower() not in lower]
    results['mentions'] = (not absent, 'absent: ' + ', '.join(absent) if absent else 'ok')
    invented = [m for m in expect['must_not_mention'] if m.lower() in lower]
    results['no_invention'] = (not invented, 'found: ' + ', '.join(invented) if invented else 'ok')
    marked = [t for t in texts if from_plan.TBC.lower() in t.lower()] + plan['unknowns']
    unmarked = [u for u in expect['must_mark_unknown'] if not any(u.lower() in t.lower() for t in marked)]
    results['unknowns'] = (not unmarked, 'not marked: ' + ', '.join(unmarked) if unmarked else 'ok')
    found = claims.find(preset) if preset else []
    results['claims'] = (not found, f'{len(found)} to confirm: ' + ', '.join(f['match'] for f in found[:5]) if found else 'ok')
    return results

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--live', action='store_true', help='Draft each brief with Claude now (one paid API call each)')
    parser.add_argument('--record', action='store_true', help='With --live, save drafts to evals/recorded/')
    parser.add_argument('--only', help='Run one brief by name')
    parser.add_argument('--min-score', type=float, default=0.0, help='Exit 1 if the average score is below this (0-1)')
    args = parser.parse_args(argv)
    if args.record and not args.live:
        parser.error('--record needs --live.')
    registry = json.loads((ROOT / 'data/modules.json').read_text())
    briefs = sorted(p for p in BRIEFS.glob('*.md') if not args.only or p.stem == args.only)
    if not briefs:
        parser.error('No briefs found.')
    if args.live:
        print(f'Live run: {len(briefs)} paid API call(s).', file=sys.stderr)
    scores, rows = [], []
    for brief in briefs:
        expect = json.loads(brief.with_suffix('.expect.json').read_text())
        if args.live:
            import draft_plan
            plan = draft_plan.request(brief.read_text(), registry)
            if args.record:
                RECORDED.mkdir(exist_ok=True)
                (RECORDED / f'{brief.stem}.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')
        else:
            saved = RECORDED / f'{brief.stem}.json'
            if not saved.is_file():
                print(f'{brief.stem}: no saved draft (run with --live --record once)', file=sys.stderr)
                continue
            plan = json.loads(saved.read_text())
        results = grade(plan, expect, registry)
        score = sum(ok for ok, _ in results.values()) / 8
        scores.append(score)
        rows.append(dict(brief=brief.stem, score=score, checks={k: dict(passed=ok, detail=d) for k, (ok, d) in results.items()}))
        print(f'{brief.stem}: {score:.2f}')
        for check, (ok, detail) in results.items():
            print(f'  {"pass" if ok else "FAIL"}  {check}: {detail}')
    if not scores:
        parser.error('Nothing to score. Run with --live, or add drafts to evals/recorded/.')
    average = sum(scores) / len(scores)
    out = ROOT / 'reports/evals'
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (out / f'{stamp}.json').write_text(json.dumps(dict(live=args.live, average=average, results=rows), indent=2) + '\n')
    print(f'Average {average:.2f} over {len(scores)} brief(s). Report: reports/evals/{stamp}.json')
    return 1 if average < args.min_score else 0

if __name__ == '__main__':
    sys.exit(main())
