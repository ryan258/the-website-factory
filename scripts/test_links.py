#!/usr/bin/env python3
"""Deep links land on declared anchors; mailto: and tel: links are valid, clickable, and never mangled."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build  # noqa: E402
import check_site  # noqa: E402
import factory  # noqa: E402
import new_site  # noqa: E402

BASE = json.loads((ROOT / 'data/presets/consultant.json').read_text())

def errors_for(preset):
    return [e for e in factory.validate(ROOT, extra_presets={'links-test': preset}) if e.startswith('links-test')]

def with_links(anchor=None, cta_url='/services/#questions', contact_urls=('mailto:hello@example.com', 'tel:+1 312 555 0100')):
    preset = copy.deepcopy(BASE)
    if anchor is not None:
        for section in preset['pages']['services']['sections']:
            if section['module'] == 'faq':
                section['anchor'] = anchor
    preset['sections']['cta']['action']['url'] = cta_url
    items = preset['sections']['contact']['items']
    for item, url in zip(items, contact_urls):
        item['url'] = url
    return preset

class ValidationTests(unittest.TestCase):
    def test_deep_link_needs_a_declared_anchor(self):
        self.assertTrue(any('missing anchor /services/#questions' in e for e in errors_for(with_links())))
        self.assertEqual(errors_for(with_links(anchor='questions')), [])

    def test_anchor_names_are_checked(self):
        for bad in ('Questions', 'faq-2', '2faq', 'a b'):
            self.assertTrue(any('anchor' in e for e in errors_for(with_links(anchor=bad, cta_url='/contact/'))), bad)
        preset = with_links(anchor='questions')
        preset['pages']['services']['sections'][0]['anchor'] = 'questions'
        self.assertTrue(any('share an anchor' in e for e in errors_for(preset)))

    def test_contact_links_are_checked(self):
        for bad in ('mailto:not-an-address', 'mailto:a@b', 'tel:12', 'tel:call-me'):
            found = errors_for(with_links(anchor='questions', contact_urls=(bad,)))
            self.assertTrue(any(('mailto link' in e or 'tel link' in e) for e in found), bad)
        for good in ('mailto:hello@example.com', 'tel:+13125550100', 'tel:(312) 555-0100'):
            self.assertEqual(errors_for(with_links(anchor='questions', contact_urls=(good,))), [], good)

    def test_other_schemes_are_refused(self):
        self.assertTrue(any('must be local page paths' in e for e in errors_for(with_links(anchor='q', cta_url='javascript:alert(1)'))))

class OutputTests(unittest.TestCase):
    def test_built_copy_has_working_deep_and_contact_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'site', 'Links Co', 'consultant')
            path = dest / 'data/presets/consultant.json'
            preset = with_links(anchor='questions')
            preset['name'] = 'Links Co'
            path.write_text(json.dumps(preset, indent=2) + '\n')
            result = subprocess.run([sys.executable, str(dest / 'scripts/build.py')], cwd=dest, env=build.environment(),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            services = (dest / 'public/services/index.html').read_text()
            contact = (dest / 'public/contact/index.html').read_text()
            self.assertIn('id=questions', services)
            self.assertIn('href=/services/#questions', services)
            self.assertIn('href=mailto:hello@example.com', contact)
            self.assertIn('tel:+1%20312%20555%200100', contact)
            self.assertNotIn('ZgotmplZ', contact)

    def test_output_check_catches_bad_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / 'index.html'
            head = '<!doctype html><title>T</title><meta name="description" content="d"><meta name="robots" content="noindex">' \
                   '<link rel="canonical" href="https://example.invalid/"><h1>Hi</h1>'
            for link, expected in (('#ZgotmplZ', 'replaced as unsafe'), ('mailto:nobody', 'mailto link'), ('tel:1', 'tel link')):
                page.write_text(head + f'<a href="{link}">x</a>')
                self.assertTrue(any(expected in e for e in check_site.check(Path(tmp), noindex=True)), link)

if __name__ == '__main__':
    unittest.main()
