"""Targeted contracts for the eight added families and their planner round trips."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import mcp_server
import schemas

ROOT = Path(__file__).resolve().parents[1]
ADDITIONS = ('announcements', 'booking', 'delivery', 'access', 'eligibility',
             'downloads', 'specifications', 'updates')


class ComponentExpansionTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / 'data/modules.json').read_text())
        self.examples = json.loads((ROOT / 'data/examples.json').read_text())

    def test_each_layout_validates_and_survives_plan_compilation(self):
        for key in ADDITIONS:
            module = self.registry[key]
            self.assertEqual(len(set(module['variants'])), 3)
            for variant in module['variants']:
                with self.subTest(module=key, layout=variant):
                    plan = {'name': 'Component fixture', 'pages': [
                        {'name': 'Home', 'sections': [
                            {'kind': 'hero', 'variant': 'centered',
                             'contentVersion': 1, 'content': self.examples['hero']},
                            {'kind': module['name'], 'variant': variant,
                             'contentVersion': 1, 'content': self.examples[key]}]},
                        {'name': 'Services', 'sections': [
                            {'kind': 'hero', 'variant': 'compact',
                             'contentVersion': 1, 'content': self.examples['hero']}]},
                        {'name': 'Contact', 'sections': [
                            {'kind': 'hero', 'variant': 'compact',
                             'contentVersion': 1, 'content': self.examples['hero']}]}]}
                    result = mcp_server.compile_plan(plan)
                    self.assertTrue(result['ok'], result.get('errors'))
                    section = result['preset']['pages']['home']['sections'][1]
                    self.assertEqual((section['module'], section['variant']), (key, variant))
                    self.assertEqual(result['preset']['sections'][section['content']], self.examples[key])

    def test_structured_requirements_are_enforced(self):
        shape = schemas.generated()['preset.schema.json']
        for key in ADDITIONS:
            for field in self.registry[key].get('item_required', []):
                with self.subTest(module=key, field=field):
                    content = deepcopy(self.examples[key])
                    del content['items'][0][field]
                    errors = schemas.validate(content, shape['$defs'][f'content-{key}'], shape)
                    self.assertTrue(any(f'missing {field}' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main()
