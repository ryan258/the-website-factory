#!/usr/bin/env python3
"""Focused factory acceptance: real copies, output omission, and invalid configuration."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import factory
import new_site
import build
import check_site

ROOT=Path(__file__).resolve().parents[1]
class FactoryTests(unittest.TestCase):
    def command(self, root, *args, ok=True):
        result=subprocess.run(['python3',str(root/'scripts/build.py'),*args],env=build.environment(),capture_output=True,text=True)
        self.assertEqual(result.returncode==0,ok,result.stdout+result.stderr)
        return result
    def test_four_presets_build_at_root_and_subpath(self):
        with tempfile.TemporaryDirectory(prefix='factory-presets-') as tmp:
            for slug in ('agency','contractor','consultant','local-service'):
                with self.subTest(preset=slug):
                    dest=new_site.create(Path(tmp)/slug,'Review Studio',slug)
                    self.assertEqual(factory.validate(dest),[])
                    self.assertFalse((dest/'content/site-kit').exists())
                    self.assertEqual(len(list((dest/'data/presets').glob('*.json'))),1)
                    for prefix in ('/','/client/'):
                        self.command(dest,'--base-url','https://example.invalid'+prefix)
                        output=dest/'public'
                        self.assertEqual(check_site.check(output.resolve()),[])
                        self.assertFalse((output/'site-kit/index.html').exists())
                        home=(output/'index.html').read_text()
                        self.assertNotIn('site-kit/',home)
                        self.assertNotIn('TheWebsiteFactory',home)
                        original_name=json.loads((ROOT/'data/presets'/f'{slug}.json').read_text())['name']
                        for page in output.rglob('*.html'):
                            self.assertNotIn(original_name,page.read_text(),str(page))
                        self.assertIn('Review Studio',home)
                        contact=(output/'contact/index.html').read_text()
                        self.assertIn('disabled',contact)
                        self.assertIn('hello@example.invalid',contact)
                        if slug!='agency':
                            self.assertFalse((output/'work/index.html').exists())
                            self.assertFalse((output/'pricing/index.html').exists())
                            self.assertNotIn('/work/',home)
                            self.assertNotIn('/pricing/',(output/'sitemap.xml').read_text())
                            self.assertNotIn('Website design',contact)
    def test_removed_page_and_module_disappear_on_rebuild(self):
        with tempfile.TemporaryDirectory(prefix='factory-remove-') as tmp:
            dest=new_site.create(Path(tmp)/'client','Review Studio','agency')
            self.command(dest)
            path=dest/'data/presets/agency.json';profile=json.loads(path.read_text())
            profile['pages'].pop('pricing')
            sections=[s for s in profile['pages']['home']['sections'] if s['module']!='process']
            profile['pages']['home']['sections']=sections
            # Reorder actual sections and give the remaining copy a distinctive test marker.
            def position(module): return next(i for i,s in enumerate(sections) if s['module']==module)
            services,work=position('services'),position('work')
            sections[services],sections[work]=sections[work],sections[services]
            profile['sections'][sections[work]['content']]['title']='Selected services marker'
            path.write_text(json.dumps(profile))
            self.command(dest)
            output=dest/'public';home=(output/'index.html').read_text()
            self.assertFalse((output/'pricing/index.html').exists())
            self.assertNotIn('/pricing/',(output/'sitemap.xml').read_text())
            self.assertNotIn('data-module=process',home)
            self.assertLess(home.index('data-module=work'),home.index('data-module=services'))
            self.assertIn('Selected services marker',home)
            self.assertEqual(check_site.check(output.resolve()),[])
    def test_configuration_errors_fail_before_output_changes(self):
        with tempfile.TemporaryDirectory(prefix='factory-invalid-') as tmp:
            dest=new_site.create(Path(tmp)/'client','Review Studio','agency')
            self.command(dest)
            output=dest/'public/index.html';digest=hashlib.sha256(output.read_bytes()).hexdigest()
            path=dest/'data/presets/agency.json';original=json.loads(path.read_text())
            mutations=[lambda p:p['pages']['home']['sections'][1].update(module='unknown'),
                       lambda p:p['pages']['home']['sections'][1].update(variant='unknown'),
                       lambda p:p['sections']['services'].pop('items'),
                       lambda p:p['pages'].pop('work'),
                       lambda p:p['sections']['hero']['action'].update(url='/absent/'),
                       lambda p:p['sections']['hero']['action'].update(url='javascript:alert(1)'),
                       lambda p:p['pages']['home']['sections'].reverse()]
            for mutate in mutations:
                profile=copy.deepcopy(original);mutate(profile);path.write_text(json.dumps(profile))
                self.command(dest,ok=False)
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),digest)
    def test_workshop_omitted_and_rebuild_removes_old_routes(self):
        with tempfile.TemporaryDirectory(prefix='factory-workshop-') as tmp:
            source=Path(tmp)/'source'
            import shutil
            shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('public','public-workshop','resources','reports','__pycache__','.tools','node_modules'))
            self.command(source)
            storefront=(source/'public/index.html').read_bytes()
            configuration=(source/'data/factory.json').read_bytes()
            self.command(source,'--workshop','--base-url','https://example.invalid/internal/')
            self.assertTrue((source/'public-workshop/site-kit/index.html').exists())
            self.assertEqual((source/'public/index.html').read_bytes(),storefront)
            self.assertEqual((source/'data/factory.json').read_bytes(),configuration)
            self.assertNotIn('site-kit/',(source/'public-workshop/index.html').read_text())
            self.command(source,'--workshop','--destination','public',ok=False)
            path=source/'data/factory.json';config=json.loads(path.read_text());config['workshop']=True;path.write_text(json.dumps(config))
            self.command(source)
            self.assertTrue((source/'public/site-kit/index.html').exists())
            self.assertNotIn('site-kit',(source/'public/sitemap.xml').read_text())
            path=source/'data/factory.json';config=json.loads(path.read_text());config['workshop']=False;path.write_text(json.dumps(config))
            self.command(source)
            self.assertFalse((source/'public/site-kit/index.html').exists())
            self.assertNotIn('site-kit',(source/'public/index.html').read_text())
    def test_scaffold_rejects_unknown_preset_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'client'
            with self.assertRaises(ValueError):new_site.create(dest,'Test','absent')
            self.assertFalse(dest.exists())
    def test_output_reconciliation_preserves_unknown_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';source.mkdir();(source/'index.html').write_text('new')
            dest=Path(tmp)/'output';dest.mkdir();(dest/'notes.txt').write_text('owner notes')
            (dest/'old.html').write_text('unknown page')
            with self.assertRaises(ValueError):build.publish_output(source,dest)
            self.assertEqual((dest/'old.html').read_text(),'unknown page')
            self.assertEqual((dest/'notes.txt').read_text(),'owner notes')
            self.assertFalse((dest/'index.html').exists())
    def test_output_reconciliation_refuses_untracked_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';source.mkdir();(source/'index.html').write_text('new')
            dest=Path(tmp)/'output';dest.mkdir();(dest/'old.js').write_text('console.log(1)')
            with self.assertRaises(ValueError) as caught:build.publish_output(source,dest)
            self.assertIn('old.js: untracked JS would remain',str(caught.exception))
    def test_parent_file_conflict_leaves_destination_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);source=tmp/'source';(source/'z-assets').mkdir(parents=True)
            (source/'index.html').write_text('new');(source/'z-assets/main.css').write_text('body{}')
            dest=tmp/'output';dest.mkdir();(dest/'z-assets').write_text('owner file')
            before={p:p.read_bytes() for p in dest.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError) as caught:build.publish_output(source,dest)
            self.assertIn('exists as a file, not a directory',str(caught.exception))
            self.assertEqual({p:p.read_bytes() for p in dest.rglob('*') if p.is_file()},before)
            self.assertFalse((dest/'index.html').exists())
            self.assertFalse((dest/'.factory-build.json').exists())
    def test_interrupted_publication_leaves_an_owned_recoverable_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);source=tmp/'source';source.mkdir()
            for name in ('a.html','b.html','c.html'):(source/name).write_text(name)
            dest=tmp/'output'
            import shutil as shutil_module
            original=shutil_module.copy2;copied=[]
            def fail_after_one(src,target,*args,**kwargs):
                if len(copied)>=1:raise OSError('device full')
                copied.append(target);return original(src,target,*args,**kwargs)
            build.shutil.copy2=fail_after_one
            try:
                with self.assertRaises(OSError):build.publish_output(source,dest)
            finally:
                build.shutil.copy2=original
            manifest=json.loads((dest/'.factory-build.json').read_text())
            landed={p.name for p in dest.glob('*.html')}
            self.assertEqual(set(manifest),landed,'the manifest must describe exactly what landed')
            for name,digest in manifest.items():
                self.assertEqual(build.digest(dest/name),digest)
            # A rerun now owns the partial output and completes it instead of refusing it.
            build.publish_output(source,dest)
            self.assertEqual({p.name for p in dest.glob('*.html')},{'a.html','b.html','c.html'})
    def test_output_reconciliation_refuses_unowned_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';source.mkdir();(source/'index.html').write_text('new')
            def fresh(setup):
                dest=Path(tempfile.mkdtemp(dir=tmp));setup(dest);return dest
            # An owner edit to a previously generated file that this build emits again.
            def edited(dest):
                (dest/'index.html').write_text('owner edit')
                (dest/'.factory-build.json').write_text(json.dumps({'index.html':hashlib.sha256(b'old').hexdigest()}))
            # A file never tracked by the factory sitting where generated output would land.
            untracked=lambda dest:(dest/'index.html').write_text('owner page')
            # A directory occupying a generated file path.
            collision=lambda dest:(dest/'index.html').mkdir()
            symlinked=lambda dest:(dest/'.factory-build.json').symlink_to(Path(tmp)/'sibling.json')
            (Path(tmp)/'sibling.json').write_text('owner data')
            for setup in (edited,untracked,collision,symlinked):
                with self.subTest(setup=setup):
                    dest=fresh(setup);before={p:p.read_bytes() for p in dest.rglob('*') if p.is_file()}
                    with self.assertRaises(ValueError):build.publish_output(source,dest)
                    self.assertEqual({p:p.read_bytes() for p in dest.rglob('*') if p.is_file()},before)
                    self.assertEqual((Path(tmp)/'sibling.json').read_text(),'owner data')
            # A clean destination still publishes, and an unchanged rebuild is accepted.
            dest=Path(tmp)/'clean';build.publish_output(source,dest);build.publish_output(source,dest)
            self.assertEqual((dest/'index.html').read_text(),'new')
if __name__=='__main__': unittest.main()
