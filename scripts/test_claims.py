#!/usr/bin/env python3
"""scripts/claims.py flags unbacked claims, respects approvals and negations, and copies drop approvals."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import claims  # noqa: E402
import new_site  # noqa: E402

def preset(texts, module='services', approved=None):
    data = {'name': 'T', 'pages': {'home': {'title': 'Home', 'description': 'd',
                                            'sections': [{'module': module, 'variant': 'cards', 'content': 'main'}]}},
            'sections': {'main': {'title': 'Main', 'items': [{'title': f'Item {i}', 'text': t} for i, t in enumerate(texts)]},
                         'unused': {'title': 'Best in town, 100% guaranteed'}}}
    if approved is not None:
        data['approved_claims'] = approved
    return data

class ClaimsTests(unittest.TestCase):
    def codes(self, data):
        return sorted({f['code'] for f in claims.find(data) if not f['approved']})

    def test_flags_each_kind(self):
        found = self.codes(preset(['From $499.', 'Saves 30% of time.', 'Trusted by 200 clients.',
                                   'Rated 4.9 stars.', 'The best bakery.']))
        self.assertEqual(found, ['CLAIM_ABSOLUTE', 'CLAIM_COUNT', 'CLAIM_PERCENT', 'CLAIM_PRICE', 'CLAIM_RATING'])

    def test_unrendered_sections_are_ignored(self):
        self.assertEqual(self.codes(preset(['Plain words.'])), [])

    def test_negations_and_questions_are_not_claims(self):
        self.assertEqual(self.codes(preset(['These are estimates, not a guarantee.', 'Do you guarantee results? No.'])), [])

    def test_approval_clears_a_claim(self):
        data = preset(['Trusted by 200 clients.'], approved=['200 clients'])
        self.assertEqual(self.codes(data), [])
        self.assertTrue(all(f['approved'] for f in claims.find(data)))

    def test_testimonials_always_need_confirmation(self):
        self.assertIn('CLAIM_TESTIMONIAL', self.codes(preset(['They were lovely.'], module='testimonials')))

    def test_selected_preset_passes_strict(self):
        self.assertEqual(claims.main(['--strict']), 0, 'the live preset has unconfirmed claims; run scripts/claims.py')

    def test_client_copy_starts_without_approvals(self):
        source = ROOT / 'data/presets/consultant.json'
        original = source.read_text()
        data = json.loads(original)
        data['approved_claims'] = ['Anything']
        source.write_text(json.dumps(data, indent=2) + '\n')
        self.addCleanup(source.write_text, original)
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'client', 'Copy Co', 'consultant')
            self.assertNotIn('approved_claims', json.loads((dest / 'data/presets/consultant.json').read_text()))

if __name__ == '__main__':
    unittest.main()
