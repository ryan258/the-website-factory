#!/usr/bin/env python3
"""Owner-run verification for the review changes. No live providers or deployment.

The default runs affected unit/integration fixtures, two builds, lint and the two
planner browser suites. --full adds the remaining established local gates.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    names = ('test_review_fixes', 'test_scaffold_core', 'test_from_plan', 'test_plan_fidelity', 'test_schemas',
             'test_claims', 'test_mcp', 'test_handover', 'test_factory', 'test_starter', 'test_enquiries', 'test_smoke', 'test_doctor', 'test_ai')
    commands = [[sys.executable, f'scripts/{name}.py'] for name in names]
    commands += [['node', 'scripts/test_contact_endpoint.mjs'], [sys.executable, 'scripts/schemas.py', '--check'],
                 ['npm', 'run', '-s', 'lint'], [sys.executable, 'scripts/build.py'],
                 [sys.executable, 'scripts/build.py', '--workshop'],
                 ['node', 'scripts/check_workflow.cjs'], ['node', 'scripts/check_planner_fidelity.cjs']]
    if args.full:
        commands += [[sys.executable, 'scripts/verify.py', '--here'], ['node', 'scripts/browser-checks.cjs'],
                     ['node', 'scripts/check_workshop.cjs'], ['node', 'scripts/check_components.cjs']]
    output = ROOT / 'reports/review-verification' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True)
    records = []
    for i, command in enumerate(commands, 1):
        name = ' '.join(command)
        print(f'[{i}/{len(commands)}] {name}', flush=True)
        log = output / f'{i:02d}.log'
        with log.open('w') as stream:
            code = subprocess.call(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        records.append(dict(command=command, code=code, log=str(log)))
        (output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
        if code:
            print(f'FAILED: {name}\n' + '\n'.join(log.read_text().splitlines()[-45:]))
            print(f'Logs: {output}')
            return code
    print(f'PASS: {len(records)} commands completed. Logs: {output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
