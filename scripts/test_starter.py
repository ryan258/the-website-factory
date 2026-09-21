#!/usr/bin/env python3
"""Focused scaffold isolation and static-check failure-path tests; no network."""
import importlib.util
import html
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
scaffold=load('new_site');static=load('check_site');build=load('build')
class StarterTests(unittest.TestCase):
    def test_existing_destination_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'existing';dest.mkdir();sentinel=dest/'keep';sentinel.write_text('owner data')
            with self.assertRaises(FileExistsError):scaffold.create(dest,'Test')
            self.assertEqual(sentinel.read_text(),'owner data')
    def test_invalid_name_and_nested_destination_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'new'
            with self.assertRaises(ValueError):scaffold.create(dest,'Bad\nname')
            self.assertFalse(dest.exists())
        with self.assertRaises(ValueError):scaffold.create(ROOT/'forbidden-copy','Test')
    def test_new_instance_build_and_edited_content(self):
        with tempfile.TemporaryDirectory(prefix='starter-fixture-') as tmp:
            dest=scaffold.create(Path(tmp)/'client','Cedar & Stone')
            for excluded in ['.tools','node_modules','public','resources','reports','.git']:
                self.assertFalse((dest/excluded).exists(),excluded)
            self.assertFalse(list(dest.rglob('__pycache__')))
            self.assertNotIn('97', (dest/'docs/acceptance.md').read_text())
            config=dest/'data/site.yaml';text=config.read_text().replace('#ffc400','#78e3bd');config.write_text(text)
            case=dest/'content/work/fieldwork.md';text=case.read_text().replace('3.8 s','6.2 s').replace('120 KB','92 KB');case.write_text(text)
            env=build.environment()
            result=subprocess.run(['python3',str(dest/'scripts/build.py'),'--base-url','https://example.invalid/client/'],cwd=tmp,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(static.check((dest/'public').resolve()),[])
            home=(dest/'public/index.html').read_text()
            self.assertIn('Cedar & Stone',html.unescape(home))
            self.assertIn('href=/client/contact/',home)
            self.assertNotIn('TheWebsiteFactory',home)
            self.assertIn('/client/fonts/inter-latin-variable.woff2',home)
            css=''.join(p.read_text() for p in (dest/'public/css').glob('*.css'))
            self.assertIn('#78e3bd',css)
            self.assertIn('/client/fonts/inter-latin-variable.woff2',css)
            detail=(dest/'public/work/fieldwork/index.html').read_text()
            self.assertIn('6.2 s',detail);self.assertIn('92 KB',detail)
            contact=(dest/'public/contact/index.html').read_text()
            self.assertIn('disabled',contact);self.assertNotIn('hello@thewebsitefactory.com',contact)
            # Mutate an emitted page to prove the checker catches a broken reference.
            page=dest/'public/index.html';page.write_text(home+'<a href="/client/missing/">broken</a>')
            self.assertTrue(any('missing' in error for error in static.check((dest/'public').resolve())))
    def test_empty_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:self.assertTrue(static.check(Path(tmp)))
if __name__=='__main__':unittest.main()
