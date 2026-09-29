#!/usr/bin/env python3
"""JSON Schemas stay current and agree with the presets; --json reports stay machine-readable."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_site  # noqa: E402
import factory  # noqa: E402
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

    def test_errors_carry_code_pointer_and_hint(self):
        # An agent repairs a field it can find: every broken input below must name the field (a JSON
        # pointer that resolves in the preset) and say what to do, not only describe the problem.
        base = json.loads((ROOT / 'data/presets/consultant.json').read_text())
        registry = json.loads((ROOT / 'data/modules.json').read_text())
        def edit(change):
            preset = copy.deepcopy(base)
            change(preset)
            return preset, [e for e in factory.validate(ROOT, extra_presets={'probe': preset}) if e.startswith('probe')]
        def resolve(document, pointer):
            for part in [p for p in pointer.split('/') if p]:
                document = document[int(part)] if isinstance(document, list) else document[part]
            return document
        services = base['pages']['home']['sections'][1]['content']
        cases = {
            'MODULE_VARIANT_UNKNOWN': lambda p: p['pages']['home']['sections'][1].update(variant='nope'),
            'MODULE_UNKNOWN': lambda p: p['pages']['home']['sections'][1].update(module='nope'),
            'PRESET_TONE_UNKNOWN': lambda p: p.update(tone='pink'),
            'PRESET_HERO_POSITION': lambda p: p['pages']['home']['sections'].reverse(),
            'CONTENT_FIELD_MISSING': lambda p: p['sections'][services].pop('title'),
            'CONTENT_ITEM_INVALID': lambda p: p['sections'][services]['items'][0].pop('text'),
            'CONTENT_LINK_INVALID': lambda p: p['sections'][services].__setitem__('action', {'label': 'Go', 'url': '/nowhere/'}),
        }
        for code, change in cases.items():
            with self.subTest(code=code):
                preset, errors = edit(change)
                found = [e for e in errors if e.code == code]
                self.assertTrue(found, f'{code} not reported: {errors}')
                issue = report.diagnostic(found[0])
                self.assertTrue(issue.get('hint'), 'a hint says what to do')
                self.assertIn('path', issue)
                # The pointer lands on the field at fault (or, for a missing one, its parent).
                resolve(preset, issue['path'].rsplit('/', 1)[0] if code == 'CONTENT_FIELD_MISSING' else issue['path'])
        # A hint names the real options, not a placeholder.
        _, errors = edit(cases['MODULE_VARIANT_UNKNOWN'])
        hint = next(e.hint for e in errors if e.code == 'MODULE_VARIANT_UNKNOWN')
        for variant in registry['services']['variants']:
            self.assertIn(variant, hint)

    def test_a_missing_content_entry_points_at_the_sections_own_field(self):
        preset = json.loads((ROOT / 'data/presets/consultant.json').read_text())
        del preset['pages']['home']['sections'][1]['content']
        preset['pages']['home']['sections'][2]['content'] = 'ghost'
        found = [e for e in factory.validate(ROOT, extra_presets={'probe': preset}) if e.startswith('probe') and e.code == 'CONTENT_TYPE_INVALID']
        self.assertEqual([e.path for e in found], ['/pages/home/sections/1/content', '/pages/home/sections/2/content'])
        self.assertIn('"ghost"', found[1].hint)

    def test_an_issue_survives_copy_and_pickle(self):
        import pickle
        issue = report.Issue('x: unknown variant', 'MODULE_VARIANT_UNKNOWN', '/a', 'hint')
        for clone in (copy.copy(issue), copy.deepcopy(issue), pickle.loads(pickle.dumps(issue))):
            self.assertEqual((str(clone), clone.code, clone.path, clone.hint), (str(issue), issue.code, issue.path, issue.hint))

    def test_typed_codes_never_disagree_with_the_pattern_map(self):
        # Codes agents already branch on must not change when an error site becomes typed. A typed
        # code may improve on the generic fallback ("ERROR"), never contradict a specific one.
        base = json.loads((ROOT / 'data/presets/agency.json').read_text())
        broken = copy.deepcopy(base)
        broken['tone'] = 'pink'
        broken['palette'] = 'nope'
        broken['pages']['home']['sections'][1]['variant'] = 'nope'
        broken['pages']['home']['sections'].append({'module': 'ghost', 'variant': 'x', 'content': 'x'})
        broken['pages']['about'] = {'title': '', 'description': '', 'sections': []}
        errors = [e for e in factory.validate(ROOT, extra_presets={'probe': broken}) if e.startswith('probe')]
        self.assertGreaterEqual(len(errors), 5)
        for issue in errors:
            with self.subTest(message=str(issue)[:60]):
                self.assertNotEqual(issue.code, 'ERROR')
                self.assertIn(report.code_for(str(issue)), (issue.code, 'ERROR'))

    def test_schema_diagnostics_get_a_pointer_from_their_prefix(self):
        self.assertEqual(report.diagnostic('$.pages[0].sections[1].title: expected string')['path'], '/pages/0/sections/1/title')
        self.assertNotIn('path', report.diagnostic('No 404.html in the build root'))

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

    def test_indexable_build_accepts_an_enabled_form_however_the_flag_is_written(self):
        # Hugo minifies data-enabled="true" to data-enabled=true; the gate must see the form either way.
        head = ('<!doctype html><title>T</title><meta name="description" content="d">'
                '<link rel="canonical" href="https://real.example/"><h1>Hi</h1>')
        for flag in ('data-enabled=true', 'data-enabled="true"', "data-enabled='true'"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / 'index.html').write_text(head + f'<form name=x {flag}></form>')
                errors = check_site.check(Path(tmp), noindex=False)
                self.assertFalse(any('no usable enquiry path' in e for e in errors), errors)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'index.html').write_text(head + '<form name=x data-enabled=false></form>')
            self.assertTrue(any('no usable enquiry path' in e for e in check_site.check(Path(tmp), noindex=False)),
                            'a disabled form is still not an enquiry path')

    def test_malformed_input_returns_diagnostics_instead_of_crashing(self):
        # validate_preset(None) raised AttributeError and a numeric image raised TypeError inside
        # Path(); a stack trace tells a caller nothing about which field was wrong.
        import mcp_server
        broken = {'name': 'X', 'label': 'X', 'tone': 'yellow', 'description': 'd',
                  'pages': {'home': {'title': 'H', 'description': 'd',
                                     'sections': [{'module': 'hero', 'variant': 'split', 'content': 'c'}]}},
                  'sections': {'c': {'title': 'T', 'intro': 'i', 'image': 123, 'imageAlt': 'a',
                                     'action': {'label': 'L', 'url': '/'}}}}
        corpus = [None, 'text', [], 123, True, {}, {'pages': 'x', 'sections': {}},
                  {'pages': {}, 'sections': 'x'}, {'pages': {'home': None}, 'sections': {}},
                  {'pages': {'home': {'sections': 'x'}}, 'sections': {}},
                  {'pages': {'home': {'sections': [None]}}, 'sections': {}}, broken]
        for case in corpus:
            with self.subTest(case=repr(case)[:40]):
                result = mcp_server.validate_preset(case)
                self.assertFalse(result['ok'])
                self.assertTrue(result['errors'])
                self.assertNotIn('ERROR', {e['code'] for e in result['errors']},
                                 'every diagnostic needs a code more specific than ERROR')

    def test_schema_diagnostics_have_stable_codes(self):
        # These were inferred from prose: "$: missing name" was reported as a broken output
        # reference, and a wrong shape fell through to the generic code.
        for message, code in [('$: expected object', 'SCHEMA_TYPE_INVALID'),
                              ('$: missing name', 'SCHEMA_FIELD_MISSING'),
                              ('$.pages: unexpected field x', 'SCHEMA_FIELD_UNKNOWN'),
                              ("$.pages.home.sections[0].variant: 'nope' is not one of ['split']",
                               'SCHEMA_VALUE_INVALID'),
                              ('$.name: must not be empty', 'SCHEMA_VALUE_INVALID')]:
            self.assertEqual(report.code_for(message), code, message)
        # Checker prose must not be captured by the schema patterns.
        self.assertEqual(report.code_for('258webco/home/hero: unknown variant nope'), 'MODULE_VARIANT_UNKNOWN')
        self.assertEqual(report.code_for('index.html: missing /images/x.png'), 'OUTPUT_REFERENCE_BROKEN')

    def test_release_needs_an_error_page(self):
        head = ('<title>T</title><meta name="description" content="D">'
                '<link rel="canonical" href="https://example.invalid/"><meta name="robots" content="noindex">')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'index.html').write_text(head + '<h1>H</h1>')
            errors = check_site.check(out, noindex=True)
            self.assertTrue(any('No 404.html' in e for e in errors), errors)
            self.assertEqual(report.code_for(next(e for e in errors if 'No 404.html' in e)),
                             'RELEASE_ERROR_PAGE_MISSING')
            (out / '404.html').write_text(head.replace('example.invalid/', 'example.invalid/404.html')
                                         + '<h1>H</h1>')
            self.assertFalse(any('404' in e for e in check_site.check(out, noindex=True)))
            # The error page stays out of the index even in a public release.
            self.assertFalse(any('404.html: noindex present' in e for e in check_site.check(out, noindex=False)))

    def test_every_release_reference_is_verified(self):
        # srcset sources, social images and same-origin absolute URLs all used to pass unchecked.
        head = ('<title>T</title><meta name="description" content="D">'
                '<link rel="canonical" href="https://example.invalid/"><meta name="robots" content="noindex">')
        cases = {
            '/images/missing-large.webp':
                '<picture><source srcset="/images/small.webp 560w, /images/missing-large.webp 1120w">'
                '<img src="/images/small.webp"></picture>',
            'https://example.invalid/images/missing-social.png':
                '<meta property="og:image" content="https://example.invalid/images/missing-social.png">',
            '/images/missing-card.png': '<meta name="twitter:image" content="/images/missing-card.png">',
            'https://example.invalid/nowhere/': '<a href="https://example.invalid/nowhere/">Nowhere</a>',
        }
        for target, markup in cases.items():
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                (out / 'index.html').write_text(head + '<h1>H</h1>' + markup)
                (out / '404.html').write_text(head.replace('example.invalid/', 'example.invalid/404.html')
                                              + '<h1>H</h1>')
                (out / 'images').mkdir()
                (out / 'images/small.webp').write_bytes(b'x')
                errors = check_site.check(out, noindex=True)
                self.assertTrue(any(target in e and 'missing' in e for e in errors),
                                f'{target} should be reported as missing: {errors}')

    def test_stylesheet_references_are_verified(self):
        head = ('<title>T</title><meta name="description" content="D">'
                '<link rel="canonical" href="https://example.invalid/client/"><meta name="robots" content="noindex">')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'index.html').write_text(head + '<h1>H</h1>')
            (out / '404.html').write_text(head.replace('/client/', '/client/404.html') + '<h1>H</h1>')
            (out / 'css').mkdir()
            (out / 'fonts').mkdir()
            (out / 'fonts/present.woff2').write_bytes(b'x')
            # A site published under a subdirectory carries its base path in stylesheet URLs.
            (out / 'css/main.css').write_text('@font-face{src:url(/client/fonts/present.woff2)}'
                                              'body{background:url(/client/images/gone.png)}')
            errors = check_site.check(out, noindex=True)
            self.assertTrue(any('css/main.css' in e and 'gone.png' in e for e in errors), errors)
            self.assertFalse(any('present.woff2' in e for e in errors), errors)

if __name__ == '__main__':
    unittest.main()
