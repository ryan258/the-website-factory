#!/usr/bin/env python3
"""Focused scaffold isolation and static-check failure-path tests; no network."""
import importlib.util
import html
import os
import re
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
    def test_compiled_preset_can_start_a_client_copy(self):
        # A preset written by from_plan.py is not in any fixed list; the scaffold must accept it.
        compiled=ROOT/'data/presets/zz-compiled-fixture.json'
        self.assertFalse(compiled.exists())
        compiled.write_text((ROOT/'data/presets/consultant.json').read_text())
        self.addCleanup(compiled.unlink)
        self.assertIn('zz-compiled-fixture',scaffold.available_presets())
        with tempfile.TemporaryDirectory() as tmp:
            dest=scaffold.create(Path(tmp)/'client','Compiled Client','zz-compiled-fixture')
            self.assertEqual([p.name for p in (dest/'data/presets').iterdir()],['zz-compiled-fixture.json'])
        with self.assertRaises(ValueError):scaffold.create(Path(tempfile.gettempdir())/'never-made','Test','no-such-preset')
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
    def test_copy_inherits_no_deployment_resources(self):
        with tempfile.TemporaryDirectory(prefix='starter-isolation-') as tmp:
            dest=scaffold.create(Path(tmp)/'client','Cedar & Stone','contractor')
            master=(ROOT/'wrangler.toml').read_text()
            # Whatever the master is configured with today: ids, buckets, addresses, project name.
            secrets={m for m in re.findall(r'(?m)^\s*(?:id|bucket_name|destination_address|ENQUIRY_TO|ENQUIRY_FROM)\s*=\s*"([^"]+)"',master)}
            # The Pages project name is also a preset name the copied README may list, so it
            # only counts as inherited if the copy would deploy to it.
            project=re.search(r'(?m)^name\s*=\s*"([^"]+)"',master).group(1)
            self.assertNotIn(f'"{project}"',(dest/'wrangler.toml').read_text())
            self.assertNotIn(f'--project-name {project}\n',(dest/'docs/cloudflare-setup.md').read_text())
            secrets|=set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+',master))
            self.assertTrue(secrets,'the master must actually be configured for this test to mean anything')
            copied=[p for p in dest.rglob('*') if p.is_file() and p.suffix in ('.toml','.md','.json','.yaml')]
            for path in copied:
                text=path.read_text(errors='ignore')
                for secret in secrets:
                    if secret in ('public','true'): continue
                    self.assertNotIn(secret,text,f'{path.relative_to(dest)} carries master value {secret!r}')
            wrangler=(dest/'wrangler.toml').read_text()
            self.assertNotIn('\n[[kv_namespaces]]',wrangler)
            self.assertNotIn('\n[vars]',wrangler)
            self.assertIn('ENQUIRY_ENABLED',wrangler)  # documented, deliberately not set
            site=(dest/'data/site.yaml').read_text()
            self.assertNotIn('Chicago',site,'the master business location must not carry into a copy')
            self.assertIn('organization: {"type": "Organization"}',site)
            guide=(dest/'docs/cloudflare-setup.md').read_text()
            self.assertIn('Cedar & Stone',guide)
            self.assertNotIn('Email Routing',guide)
    def test_empty_output_fails(self):
        with tempfile.TemporaryDirectory() as tmp:self.assertTrue(static.check(Path(tmp)))
if __name__=='__main__':unittest.main()
