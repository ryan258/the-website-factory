#!/usr/bin/env python3
"""JSON Schemas stay current and agree with the presets; --json reports stay machine-readable."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_site  # noqa: E402
import report  # noqa: E402
import schemas  # noqa: E402

def preset_schema():
    return json.loads((ROOT / 'schemas/preset.schema.json').read_text())

class SchemaTests(unittest.TestCase):
    def test_committed_schemas_are_current(self):
        self.assertEqual(schemas.main(['--check']), 0, 'run python3 scripts/schemas.py and commit schemas/')

    def test_every_preset_matches_the_schema(self):
        for path in (ROOT / 'data/presets').glob('*.json'):
            self.assertEqual(schemas.validate(json.loads(path.read_text()), preset_schema()), [], path.name)

    def test_schema_catches_bad_tone_variant_and_missing_page(self):
        preset = json.loads((ROOT / 'data/presets/agency.json').read_text())
        preset['tone'] = 'pink'
        preset['pages']['home']['sections'][0]['variant'] = 'nope'
        del preset['pages']['contact']
        errors = ' | '.join(schemas.validate(preset, preset_schema()))
        for expected in ('$.tone', "'nope'", 'missing contact'):
            self.assertIn(expected, errors)

    def test_plan_schema_is_structured_output_ready(self):
        plan = json.loads((ROOT / 'schemas/plan.schema.json').read_text())
        def walk(node):
            if isinstance(node, dict):
                if node.get('type') == 'object':
                    self.assertIs(node.get('additionalProperties'), False)
                    self.assertEqual(sorted(node['required']), sorted(node['properties']))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(plan)
        kinds = plan['properties']['pages']['items']['properties']['sections']['items']['properties']['kind']['enum']
        self.assertNotIn('fit', kinds, 'scope classification stays a human decision')

class JsonReportTests(unittest.TestCase):
    def test_codes_for_known_messages(self):
        self.assertEqual(report.code_for('agency/home/hero: unknown variant'), 'MODULE_VARIANT_UNKNOWN')
        self.assertEqual(report.code_for('x.html: expected one H1'), 'OUTPUT_H1_COUNT')
        self.assertEqual(report.code_for('something new'), 'ERROR')

    def test_factory_json_output(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/factory.py'), '--json'], capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual(data['ok'], result.returncode == 0)
        self.assertIsInstance(data['errors'], list)

    def test_check_site_json_reports_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_site.py'), tmp, '--json'],
                                    capture_output=True, text=True)
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(data['errors'][0]['code'], 'OUTPUT_EMPTY')

    def test_indexable_build_rejects_placeholder_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / 'index.html'
            page.write_text('<!doctype html><title>T</title><meta name="description" content="d">'
                            '<link rel="canonical" href="https://real.example/"><h1>Hi</h1><p>Hours: To be confirmed</p>')
            errors = check_site.check(Path(tmp), noindex=False)
            self.assertTrue(any('placeholder text' in e for e in errors), errors)
            page.write_text(page.read_text().replace('To be confirmed', 'Mon–Fri 9–5'))
            self.assertFalse(any('placeholder' in e for e in check_site.check(Path(tmp), noindex=False)))

    def test_indexable_build_rejects_missing_enquiry_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / 'index.html'
            page.write_text('<!doctype html><title>T</title><meta name="description" content="d">'
                            '<link rel="canonical" href="https://real.example/"><h1>Hi</h1><p>Welcome</p>')
            errors = check_site.check(Path(tmp), noindex=False)
            self.assertTrue(any('no usable enquiry path' in e for e in errors), errors)
            page.write_text(page.read_text() + '<a href="mailto:contact@real.example">Email us</a>')
            errors = check_site.check(Path(tmp), noindex=False)
            self.assertFalse(any('no usable enquiry path' in e for e in errors), errors)

if __name__ == '__main__':
    unittest.main()
