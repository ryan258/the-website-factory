"""Regression checks for the October review. Local fixtures; no provider or live intake."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build
import claims
import draft_plan
import factory
import from_plan
import handover
import mcp_server
import new_site
from output_lock import locked_output
import site_state
import smoke
import wf

ROOT = Path(__file__).resolve().parents[1]


class ReviewFixTests(unittest.TestCase):
    def test_malformed_rpc_does_not_end_the_stdio_session(self):
        messages = [dict(jsonrpc='2.0', id=1, method='initialize', params='wrong'),
                    dict(jsonrpc='2.0', id=2, method='tools/call', params={'name': []}),
                    dict(jsonrpc='2.0', id=3, method='ping')]
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/mcp_server.py')],
                                input='\n'.join(json.dumps(m) for m in messages)+'\n', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([r['id'] for r in replies], [1, 2, 3])
        self.assertEqual(replies[0]['error']['code'], -32602)
        self.assertEqual(replies[2]['result'], {})

    def test_invalid_nested_module_is_a_field_error(self):
        preset = site_state.selected(ROOT)
        preset['pages']['home']['sections'][0]['module'] = []
        result = mcp_server.validate_preset(preset)
        self.assertFalse(result['ok'])
        self.assertIn('module', json.dumps(result))
        self.assertTrue(factory.validate(ROOT, extra_presets={'invalid': preset}))

    def test_claim_scope_agrees_on_shared_contact_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'Scope Co', 'consultant')
            (root / 'data/contact.yaml').write_text('budgets: ["A $999 website"]\n')
            preset = site_state.selected(root)
            direct = claims.find(preset, root=root)
            with patch.object(mcp_server, 'ROOT', root):
                machine = mcp_server.check_claims()
            self.assertEqual(machine['scope'], 'site')
            self.assertEqual(machine['findings'], direct)
            text, ready = handover.report(root)
            self.assertFalse(ready)
            self.assertIn('$999', text)
            self.assertEqual(mcp_server.check_claims(preset=preset)['scope'], 'preset-only')

    def test_receipt_rejects_changed_sources_and_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'Receipt Co', 'consultant')
            output = root / 'public'
            output.mkdir()
            (output / 'index.html').write_text('<h1>Recorded output</h1>')
            effective = site_state.settings(root, env={'HUGO_PARAMS_FORMENABLED': 'true'}, base_url='https://release.example/')
            inputs = site_state.source_inventory(root)
            site_state.write_receipt(root, output, effective, inputs)
            receipt, errors = site_state.build_evidence(root, output)
            self.assertEqual(errors, [])
            self.assertTrue(receipt['settings']['form_enabled'])
            (root / 'data/contact.yaml').write_text('budgets: ["Changed"]\n')
            self.assertTrue(any('Source has changed' in e for e in site_state.build_evidence(root, output)[1]))
            (output / 'index.html').write_text('changed output')
            self.assertTrue(any('artifact changed' in e for e in site_state.build_evidence(root, output)[1]))

    def test_source_change_during_build_does_not_get_a_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'Race Co', 'consultant')
            inputs = site_state.source_inventory(root)
            (root / 'data/contact.yaml').write_text('budgets: ["New content"]\n')
            output = root / 'public'
            output.mkdir()
            with self.assertRaisesRegex(ValueError, 'during the build'):
                site_state.write_receipt(root, output, site_state.settings(root), inputs)
            self.assertFalse((output / site_state.RECEIPT).exists())

    def test_lock_precedes_manifest_read_or_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, destination = Path(temporary) / 'source', Path(temporary) / 'output'
            source.mkdir()
            (source / 'index.html').write_text('new')
            destination.mkdir()
            (destination / '.factory-build.json').write_text('not JSON')
            with locked_output(destination):
                with self.assertRaisesRegex(ValueError, 'lock'):
                    build.publish_output(source, destination)
            self.assertEqual((destination / '.factory-build.json').read_text(), 'not JSON')

    def test_indexable_build_stops_on_claim_before_invoking_hugo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'Release Co', 'consultant')
            (root / 'data/contact.yaml').write_text('budgets: ["A $999 website"]\n')
            result = subprocess.run([sys.executable, str(root / 'scripts/build.py'), '--json'],
                                    env={**os.environ, 'HUGO_PARAMS_NOINDEX': 'false'}, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unapproved', result.stdout)
            self.assertFalse((root / 'public').exists())

    def test_creator_contract_does_not_inject_services_or_contact(self):
        registry = json.loads((ROOT / 'data/modules.json').read_text())
        plan = dict(name='Creator', site_type='creator', contact_mode='off', pages=[
            dict(name='Home', sections=[dict(kind='hero', title='Create', body='A personal collection.',
                                            target='https://publication.example/read', cta='Read')])])
        slug, preset = from_plan.convert_plan_to_preset(plan, registry)
        self.assertEqual(list(preset['pages']), ['home'])
        self.assertEqual([s['module'] for s in preset['pages']['home']['sections']], ['hero'])
        self.assertFalse([e for e in factory.validate(ROOT, extra_presets={slug: preset}) if e.startswith(slug)])
        self.assertEqual(from_plan.action_url('https://publication.example/read', ['home'], '/', 'hero', 'home'),
                         'https://publication.example/read')
        with self.assertRaises(ValueError):
            from_plan.action_url('https://user:secret@publication.example/', ['home'], '/', 'hero', 'home')

    def test_client_docs_and_second_generation_are_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'First Creator', 'creator-portfolio')
            self.assertTrue((root / 'wf').is_file())
            self.assertTrue((root / 'AGENTS.md').is_file())
            self.assertNotIn('vertical_site.py', (root / 'README.md').read_text())
            self.assertIn('--strict', json.loads((root / 'package.json').read_text())['scripts']['test'])
            with patch.object(new_site, 'ROOT', root):
                second = new_site.create(Path(temporary) / 'second', 'Second Creator', 'creator-portfolio')
            self.assertEqual(factory.validate(second), [])
            self.assertFalse((second / 'data/content-review.json').exists())

    def test_creator_build_uses_current_preset_metadata_and_external_resources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'Creator Co', 'creator-portfolio')
            path = root / 'data/presets/creator-portfolio.json'
            preset = json.loads(path.read_text())
            preset['pages']['home']['title'] = 'Selected work'
            preset['pages']['home']['description'] = 'New editorial description after scaffolding.'
            preset['sections']['collection']['items'][0]['url'] = 'https://publication.example/work'
            path.write_text(json.dumps(preset))
            result = subprocess.run([sys.executable, str(root / 'scripts/build.py')], cwd=root,
                                    env=build.environment(), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            html = (root / 'public/index.html').read_text()
            self.assertIn('Selected work — Creator Co', html)
            self.assertIn('New editorial description after scaffolding.', html)
            self.assertIn('https://publication.example/work', html)
            self.assertNotIn('class=contact-form', html)
            self.assertFalse((root / 'public/contact').exists())
            self.assertEqual(site_state.build_evidence(root, root / 'public')[1], [])

    def test_content_review_only_invalidates_changed_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = new_site.create(Path(temporary) / 'client', 'Review Co', 'consultant')
            state = site_state.readiness(root)
            record = dict(version=1, reviewer='Fixture owner', reviewed_at='2026-10-03', fields=state['fields'])
            (root / 'data/content-review.json').write_text(json.dumps(record))
            self.assertTrue(site_state.readiness(root)['content_review_current'])
            path = root / 'data/presets/consultant.json'
            preset = json.loads(path.read_text())
            key = preset['pages']['home']['sections'][0]['content']
            preset['sections'][key]['title'] = 'Changed heading'
            path.write_text(json.dumps(preset))
            changed = site_state.readiness(root)
            self.assertFalse(changed['content_review_current'])
            self.assertEqual(changed['changed_fields'], [f'sections.{key}.title'])

    def test_oversized_model_content_is_not_silently_clipped(self):
        plan = json.loads((ROOT / 'evals/recorded/bakery.json').read_text())
        plan['pages'][0]['sections'][0]['body'] = 'x' * (draft_plan.MAX_TEXT + 1)
        registry = json.loads((ROOT / 'data/modules.json').read_text())
        with self.assertRaisesRegex(ValueError, 'no content was discarded'):
            draft_plan.to_planner(plan, registry)
        plan = copy.deepcopy(plan)
        plan['pages'] *= 31
        with self.assertRaisesRegex(ValueError, 'no content was discarded'):
            draft_plan.to_planner(plan, registry)

    def test_backup_restore_rejects_traversal_and_preserves_existing_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / 'unsafe.zip'
            with zipfile.ZipFile(archive, 'w') as saved:
                saved.writestr('../escape', 'unsafe')
            with self.assertRaises(ValueError):
                wf.restore(archive, root / 'client')
            self.assertFalse((root / 'client').exists())
            archive = root / 'safe.zip'
            with zipfile.ZipFile(archive, 'w') as saved:
                saved.writestr('README.md', 'source')
            restored = wf.restore(archive, root / 'client')
            with self.assertRaises(FileExistsError):
                wf.restore(archive, restored)
            self.assertEqual((restored / 'README.md').read_text(), 'source')

    def test_smoke_compares_expected_release_identity(self):
        with patch.object(smoke, 'fetch', return_value=(200, {}, '{"release_id":"old"}')):
            results = smoke.check_site('https://release.example', noindex=True, endpoint=False, expected_release='new')
        self.assertFalse(results[0][0])
        self.assertIn('intended artifact', results[0][1])


if __name__ == '__main__':
    unittest.main()
