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
        # The approval is the field's exact rendered text, so editing the copy revokes it.
        data = preset(['Trusted by 200 clients.'], approved=['Trusted by 200 clients.'])
        self.assertEqual(self.codes(data), [])
        self.assertTrue(all(f['approved'] for f in claims.find(data)))

    def test_a_phrase_does_not_approve_the_text_around_it(self):
        # Approving a fragment used to approve every claim in any text containing it: the word
        # "We" approved an unrelated price, count and guarantee.
        data = preset(['We charge from $499.', 'We serve 200 clients.', 'We are the best.'],
                      approved=['We'])
        self.assertEqual(self.codes(data), ['CLAIM_ABSOLUTE', 'CLAIM_COUNT', 'CLAIM_PRICE'])
        data = preset(['Trusted by 200 clients.'], approved=['200 clients'])
        self.assertEqual(self.codes(data), ['CLAIM_COUNT'])

    def test_edited_copy_loses_its_approval(self):
        approved = 'Trusted by 200 clients.'
        self.assertEqual(self.codes(preset([approved], approved=[approved])), [])
        self.assertEqual(self.codes(preset(['Trusted by 300 clients.'], approved=[approved])), ['CLAIM_COUNT'])

    def test_site_data_and_rendered_markdown_are_scanned(self):
        # A preset renders brand and form data it does not contain; scanning only the preset
        # reported zero claims for a site whose contact form offered monetary ranges.
        with tempfile.TemporaryDirectory(prefix='claims-root-') as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            (root / 'data/contact.yaml').write_text('budgets:\n  - "Under $2,400"\n')
            (root / 'data/site.yaml').write_text('tagline: "The best builder in town"\n')
            (root / 'content').mkdir()
            (root / 'content/_index.md').write_text('---\ntitle: Home\n---\nTrusted by 200 clients.\n')
            data = preset(['Plain words.'])
            self.assertEqual(self.codes(data), [], 'the preset itself states nothing to confirm')
            found = {f['code'] for f in claims.find(data, root=root) if not f['approved']}
            self.assertEqual(found, {'CLAIM_PRICE', 'CLAIM_ABSOLUTE', 'CLAIM_COUNT'})

    def test_unrendered_detail_pages_are_not_scanned(self):
        # A detail page the preset never links is pruned before Hugo sees it, so it states
        # nothing to confirm.
        with tempfile.TemporaryDirectory(prefix='claims-detail-') as tmp:
            root = Path(tmp)
            (root / 'content/services').mkdir(parents=True)
            (root / 'content/services/_index.md').write_text('---\ntitle: Services\n---\n')
            (root / 'content/services/linked.md').write_text('Rated 4.9 stars.\n')
            (root / 'content/services/orphan.md').write_text('The best in town.\n')
            data = preset(['Plain words.'])
            data['pages']['services'] = {'title': 'Services', 'description': 'd', 'sections': []}
            data['sections']['main']['items'][0]['url'] = '/services/linked/'
            found = {f['code'] for f in claims.find(data, root=root) if not f['approved']}
            self.assertIn('CLAIM_RATING', found, 'a linked detail page renders and must be scanned')
            self.assertNotIn('CLAIM_ABSOLUTE', found, 'an unlinked detail page never renders')

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
