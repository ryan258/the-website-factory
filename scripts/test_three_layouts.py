"""Validate each catalog layout through the same plan compiler used by the operator."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import mcp_server

ROOT = Path(__file__).resolve().parents[1]


class ThreeLayoutTests(unittest.TestCase):
    def test_all_families_have_three_compilable_layouts(self):
        registry = json.loads((ROOT / 'data/modules.json').read_text())
        examples = json.loads((ROOT / 'data/examples.json').read_text())
        for key, module in registry.items():
            self.assertEqual(len(module['variants']), 3, key)
            self.assertEqual(len(set(module['variants'])), 3, key)
            for variant in module['variants']:
                with self.subTest(module=key, variant=variant):
                    content = deepcopy(examples[key])
                    services = deepcopy(examples['services'])
                    if key == 'project-brief':
                        services['items'] = [{'title': title, 'text': 'Illustrative service.'}
                                             for title in content['services']]
                    section = {'kind': key, 'variant': variant,
                               'contentVersion': 1, 'content': content}
                    hero = {'kind': 'hero', 'variant': 'centered',
                            'contentVersion': 1, 'content': examples['hero']}
                    pages = [{'name': 'Home', 'sections': [section] if key == 'hero'
                              else [hero, section]}]
                    for name in ('Services', 'Work', 'Pricing', 'Contact', 'About'):
                        page = {'name': name, 'sections': [hero]}
                        if name == 'Services':
                            page['sections'] = [hero, {'kind': 'services', 'variant': 'cards',
                                                      'contentVersion': 1, 'content': services}]
                        pages.append(page)
                    result = mcp_server.compile_plan({'name': 'Layout fixture', 'pages': pages})
                    self.assertTrue(result['ok'], result.get('errors'))
                    saved = result['preset']['pages']['home']['sections'][-1]
                    self.assertEqual((saved['module'], saved['variant']), (key, variant))
                    self.assertEqual(result['preset']['sections'][saved['content']], content)


if __name__ == '__main__':
    unittest.main()
