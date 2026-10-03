#!/usr/bin/env python3
"""Targeted semantic fidelity and client resource tests; no paid or network calls."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import factory
import from_plan
import new_site

ROOT = Path(__file__).resolve().parents[1]


def planner_export(slug):
    source = json.loads((ROOT / 'data/presets' / f'{slug}.json').read_text())
    # Match the metadata carried by workflow.js createStarter, including creator modes.
    project = {key: deepcopy(source[key]) for key in
               ('name', 'label', 'tone', 'palette', 'font_pairing', 'site_type', 'contact_mode') if key in source}
    project.update(goal=source.get('description', ''), starterPreset=slug, pages=[])
    for key, page in source['pages'].items():
        sections = []
        for spec in page['sections']:
            content = deepcopy(source['sections'][spec['content']])
            action = content.get('action', {})
            sections.append(dict(kind=spec['module'], variant=spec['variant'], title=content['title'],
                                 body=content.get('intro', content.get('body', '')), cta=action.get('label', ''),
                                 target=action.get('url', ''), contentVersion=1, content=content,
                                 **({'anchor': spec['anchor']} if 'anchor' in spec else {})))
        project['pages'].append(dict(slug=key, name=page['title'], purpose=page['description'], sections=sections))
    return source, project


class PlanFidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / 'data/modules.json').read_text())

    def test_all_starters_preserve_every_renderer_field(self):
        for path in (ROOT / 'data/presets').glob('*.json'):
            if path.stem == '258webco':
                continue
            with self.subTest(starter=path.stem):
                source, project = planner_export(path.stem)
                before = deepcopy(project)
                slug, preset = from_plan.convert_plan_to_preset(project, self.registry)
                self.assertEqual(project, before, 'compilation must not mutate the backup')
                self.assertEqual(factory.validate(ROOT, extra_presets={slug: preset}), [])
                for key in ('name', 'label', 'tone', 'description', 'palette', 'font_pairing', 'site_type', 'contact_mode'):
                    self.assertEqual(preset.get(key), source.get(key), key)
                self.assertEqual(list(preset['pages']), list(source['pages']), 'page order and membership')
                for key, page in source['pages'].items():
                    output = preset['pages'][key]
                    self.assertEqual(output['description'], page['description'])
                    self.assertEqual(len(output['sections']), len(page['sections']))
                    for original, compiled in zip(page['sections'], output['sections']):
                        self.assertEqual({k: v for k, v in original.items() if k != 'content'},
                                         {k: v for k, v in compiled.items() if k != 'content'})
                        self.assertEqual(preset['sections'][compiled['content']], source['sections'][original['content']])

    def test_legacy_edit_cannot_restore_original_item_text(self):
        source, _ = planner_export('consultant')
        original = next(source['sections'][s['content']] for s in source['pages']['home']['sections'] if s['module'] == 'services')
        body = from_plan.legacy_body(original).replace(original['items'][0]['text'], 'Edited by the owner.')
        project = dict(name='Legacy edit', starterPreset='consultant', pages=[dict(name='Home', slug='home', sections=[
            dict(kind='services', title=original['title'], body=body)])])
        _, compiled = from_plan.convert_plan_to_preset(project, self.registry)
        self.assertIn('Edited by the owner.', json.dumps(compiled))

    def test_legacy_items_keep_optional_fields_and_reject_invalid_classifications(self):
        source, project = planner_export('construction')
        for page in project['pages']:
            for section in page['sections']:
                content = section.pop('content')
                section['body'] = from_plan.legacy_body(content)
                if 'items' in content:
                    section['items'] = content['items']
        _, compiled = from_plan.convert_plan_to_preset(project, self.registry)
        wanted = [i for page in source['pages'].values() for spec in page['sections']
                  for i in source['sections'][spec['content']].get('items', []) if i.get('image')]
        got = [i for s in compiled['sections'].values() for i in s.get('items', []) if i.get('image')]
        self.assertEqual(got, wanted)
        fit = next(s for p in project['pages'] for s in p['sections'] if s['kind'] == 'fit')
        fit['items'][0]['group'] = 'not-a-group'
        with self.assertRaisesRegex(ValueError, 'needs group'):
            from_plan.convert_plan_to_preset(project, self.registry)

    def test_malformed_structures_and_multiple_projects_fail_clearly(self):
        _, project = planner_export('construction')
        for value in ([], {'items': [7]}, {'items': ['wrong']}, {'action': 'wrong'}):
            with self.subTest(content=value):
                broken = deepcopy(project)
                broken['pages'][0]['sections'][0]['content'] = value
                with self.assertRaises(ValueError):
                    from_plan.convert_plan_to_preset(broken, self.registry)
        with self.assertRaisesRegex(ValueError, 'multiple projects'):
            from_plan.convert_plan_to_preset({'projects': [project, project]}, self.registry)

    def test_final_profile_is_applied_once_and_keeps_resources(self):
        _, project = planner_export('construction')
        slug, profile = from_plan.convert_plan_to_preset(project, self.registry)
        with tempfile.TemporaryDirectory() as tmp, patch.object(new_site, 'apply_preset', wraps=new_site.apply_preset) as apply:
            dest = new_site.create(Path(tmp) / 'site', profile['name'], slug, profile=profile)
            apply.assert_called_once_with(dest, slug, profile['name'])
            self.assertEqual(factory.validate(dest), [])
            for image in factory.referenced_assets(profile, dest / 'content'):
                self.assertTrue((dest / 'assets' / image).is_file(), image)
            self.assertTrue(list((dest / 'content/services').glob('*.md')))
            self.assertTrue(list((dest / 'static/fonts').glob('*source-serif*')))
            self.assertIn('noindex = true', (dest / 'hugo.toml').read_text())
            self.assertIn('formEnabled = false', (dest / 'hugo.toml').read_text())


if __name__ == '__main__':
    unittest.main()
