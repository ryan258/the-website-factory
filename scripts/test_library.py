#!/usr/bin/env python3
"""Palettes pass contrast, outside form services stay inside the CSP, and llms.txt is generated."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build  # noqa: E402
import contrast  # noqa: E402
import new_site  # noqa: E402

def run_build(root, *args, **env):
    return subprocess.run([sys.executable, str(root / 'scripts/build.py'), *args], cwd=root,
                          env={**build.environment(), **env}, capture_output=True, text=True)

class PaletteTests(unittest.TestCase):
    def test_site_theme_and_every_palette_pass(self):
        self.assertEqual(contrast.main([]), 0)

    def test_low_contrast_is_caught(self):
        theme = dict(contrast.palettes()['harbor']['colors'], muted='#b0b8c0')
        self.assertTrue(any('muted on paper' in p for p in contrast.check(theme, 'test')))
        self.assertIn('missing or invalid colors', contrast.check({'ink': '#000000'}, 'test')[0])

    def test_copy_takes_a_palette(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'c', 'Palette Co', 'clinic', 'forest')
            theme = contrast.site_theme(dest)
            self.assertEqual(theme, contrast.palettes()['forest']['colors'])
            with self.assertRaises(ValueError):
                new_site.create(Path(tmp) / 'd', 'Palette Co', 'clinic', 'no-such-palette')

class FormServiceTests(unittest.TestCase):
    def test_outside_service_is_allowed_only_in_the_built_csp(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_build(ROOT, '--destination', str(Path(tmp) / 'out'),
                               HUGO_PARAMS_FORMENABLED='true', HUGO_PARAMS_FORMACTION='https://forms.example.com/f/abc')
            self.assertEqual(result.returncode, 0, result.stderr)
            headers = (Path(tmp) / 'out/_headers').read_text()
            self.assertIn("form-action 'self' https://forms.example.com;", headers)
            self.assertIn("connect-src 'self' https://forms.example.com;", headers)
            contact = (Path(tmp) / 'out/contact/index.html').read_text()
            self.assertIn('action=https://forms.example.com/f/abc', contact)
            self.assertIn('forms.example.com', contact)
        self.assertIn("form-action 'self';", (ROOT / 'static/_headers').read_text(), 'the source CSP is unchanged')

    def test_unsafe_form_address_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ('http://forms.example.com/f', 'https://user:pw@forms.example.com/f', 'https://forms.example.com/f?x=1'):
                result = run_build(ROOT, '--destination', str(Path(tmp) / 'out'), HUGO_PARAMS_FORMACTION=bad)
                self.assertNotEqual(result.returncode, 0, bad)
                self.assertIn('formAction must be', result.stderr)

    def test_copy_does_not_inherit_a_form_service(self):
        hugo = ROOT / 'hugo.toml'
        original = hugo.read_text()
        hugo.write_text(original.replace("formAction = ''", "formAction = 'https://forms.example.com/f/master'"))
        self.addCleanup(hugo.write_text, original)
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'c', 'Form Co', 'consultant')
            self.assertIn("formAction = ''", (dest / 'hugo.toml').read_text())

class FontTests(unittest.TestCase):
    def test_every_pairing_is_self_hosted_and_licensed(self):
        import factory
        self.assertEqual(factory.font_errors(ROOT), [])
        for name, pairing in json.loads((ROOT / 'data/fonts.json').read_text()).items():
            for font in (pairing['body'], pairing.get('heading') or pairing['body']):
                path = ROOT / 'static' / font['file']
                self.assertTrue(path.is_file(), f'{name}: {font["file"]}')
                stem = path.name.replace('-latin-variable.woff2', '')
                license_file = ROOT / 'static/fonts' / ('OFL.txt' if stem == 'inter' else f'OFL-{stem}.txt')
                self.assertIn('SIL Open Font License', license_file.read_text(), name)

    def test_copy_with_a_pairing_keeps_only_its_fonts(self):
        import factory
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'c', 'Font Co', 'consultant', fonts='editorial')
            self.assertEqual(sorted(p.name for p in (dest / 'static/fonts').iterdir()),
                             ['OFL-source-serif-4.txt', 'OFL.txt', 'inter-latin-variable.woff2', 'source-serif-4-latin-variable.woff2'])
            settings = factory.font_settings(dest)
            self.assertEqual((settings['family'], settings['heading_family']), ('Inter', 'Source Serif 4'))
            self.assertEqual(factory.validate(dest), [])
            result = run_build(dest)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            css = ''.join(p.read_text() for p in (dest / 'public/css').glob('*.css'))
            self.assertIn('--heading-font:"Source Serif 4", serif', css, 'multi-word names keep their quotes')
            home = (dest / 'public/index.html').read_text()
            self.assertIn('href=/fonts/source-serif-4-latin-variable.woff2 as=font', home)
            with self.assertRaises(ValueError):
                new_site.create(Path(tmp) / 'd', 'Font Co', 'consultant', fonts='no-such-pairing')

    def test_bad_font_settings_are_caught(self):
        import factory
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'c', 'Font Co', 'consultant', fonts='warm')
            site = dest / 'data/site.yaml'
            original = site.read_text()
            for old, new, expected in (('"Fraunces"', '"Fraunces; }"', 'plain font name'),
                                       ('heading_fallback: "serif"', 'heading_fallback: "cursive"', 'serif or sans-serif'),
                                       ('tracking: "-.02em"', 'tracking: "tight"', 'em value')):
                site.write_text(original.replace(old, new))
                self.assertTrue(any(expected in e for e in factory.validate(dest)), expected)
            site.write_text(original)
            (dest / 'static/fonts/OFL-fraunces.txt').unlink()
            self.assertTrue(any('no license file' in e for e in factory.validate(dest)))

    def test_heavy_font_preloads_fail_the_output_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'fonts').mkdir()
            (out / 'fonts/big.woff2').write_bytes(b'0' * 95000)
            (out / 'index.html').write_text('<!doctype html><title>T</title><meta name="description" content="d">'
                                            '<meta name="robots" content="noindex"><link rel="canonical" href="https://example.invalid/">'
                                            '<link rel="preload" href="/fonts/big.woff2" as="font"><h1>Hi</h1>')
            import check_site
            self.assertTrue(any('preloaded fonts' in e for e in check_site.check(out, noindex=True)))

class LlmsTxtTests(unittest.TestCase):
    def test_llms_txt_lists_selected_pages_in_menu_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_build(ROOT, '--destination', str(Path(tmp) / 'out'))
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (Path(tmp) / 'out/llms.txt').read_text()
        preset = json.loads((ROOT / 'data/presets/258webco.json').read_text())
        self.assertTrue(text.startswith(f'# {preset["name"]}\n'))
        links = [line for line in text.splitlines() if line.startswith('- [')]
        self.assertEqual(len(links), len(preset['pages']))
        self.assertLess(text.index('[Home]'), text.index('[Services]'))
        self.assertLess(text.index('[Contact]'), text.index('[Privacy]'))
        self.assertIn('This is a preview', text)

if __name__ == '__main__':
    unittest.main()
