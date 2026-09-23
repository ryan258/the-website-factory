#!/usr/bin/env python3
"""The eval grader passes a careful draft and catches invented facts and hidden gaps."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import eval_plans  # noqa: E402

REGISTRY = json.loads((ROOT / 'data/modules.json').read_text())
GOOD = json.loads((ROOT / 'evals/recorded/bakery.json').read_text())
EXPECT = json.loads((ROOT / 'evals/briefs/bakery.expect.json').read_text())

class EvalTests(unittest.TestCase):
    def failed(self, plan):
        return sorted(k for k, (ok, _) in eval_plans.grade(plan, EXPECT, REGISTRY).items() if not ok)

    def test_careful_draft_passes_every_check(self):
        self.assertEqual(self.failed(GOOD), [])

    def test_invented_facts_and_hidden_gaps_fail(self):
        bad = copy.deepcopy(GOOD)
        services = bad['pages'][0]['sections'][1]
        services['body'] = services['body'].replace('Made to order', 'Award-winning cakes from $45, made to order')
        contact = bad['pages'][2]['sections'][1]
        contact['body'] = 'Opening hours - Monday to Saturday, 7am to 3pm.'
        bad['unknowns'] = []
        self.assertEqual(self.failed(bad), ['claims', 'no_invention', 'unknowns'])

    def test_off_schema_draft_fails_fast(self):
        self.assertEqual(self.failed({'name': 'X'}), ['schema'])

    def test_every_brief_has_expectations(self):
        for brief in (ROOT / 'evals/briefs').glob('*.md'):
            expect = json.loads(brief.with_suffix('.expect.json').read_text())
            self.assertLessEqual(expect['min_pages'], expect['max_pages'], brief.name)
            self.assertTrue(set(expect['required_modules']) <= set(REGISTRY), brief.name)

    def test_offline_run_meets_the_bar(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/eval_plans.py'), '--min-score', '1.0'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('bakery: 1.00', result.stdout)

if __name__ == '__main__':
    unittest.main()
