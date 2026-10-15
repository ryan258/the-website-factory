#!/usr/bin/env python3
"""Eject: a plain Hugo copy with no factory attached, proven to build the same site. Local only."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


new_site, build = load('new_site'), load('build')
GONE = ('scripts', 'schemas', 'wf', '.mcp.json', 'AGENTS.md', 'factory-capabilities.json', 'package.json',
        'data/modules.json', 'data/examples.json', 'data/tones.json', 'layouts/_default/catalog.html',
        'layouts/_default/kit.html', 'assets/js/workflow.js')


class EjectTests(unittest.TestCase):
    def eject(self, client, destination, *flags):
        return subprocess.run([sys.executable, str(client / 'scripts/eject.py'), str(destination), *flags],
                              env=build.environment(), capture_output=True, text=True)

    def test_client_copy_ejects_to_plain_hugo(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = new_site.create(Path(temporary) / 'client', 'Eject Co', 'consultant')
            refused = self.eject(client, Path(temporary) / 'out')
            self.assertNotEqual(refused.returncode, 0, 'a new copy still has sample text')
            self.assertIn('To be confirmed', refused.stderr + refused.stdout)
            self.assertFalse((Path(temporary) / 'out').exists())
            result = self.eject(client, Path(temporary) / 'out', '--draft')
            self.assertEqual(result.returncode, 0, result.stderr)
            out = Path(temporary) / 'out'
            for name in GONE:
                self.assertFalse((out / name).exists(), name)
            self.assertNotIn('hugo.Data.modules', (out / 'layouts/partials/factory/module.html').read_text())
            self.assertEqual([p.name for p in (out / 'data/presets').iterdir()], ['consultant.json'])
            self.assertIn('hugo --minify', (out / 'README.md').read_text())
            self.assertNotIn('scripts/', (out / 'docs/cloudflare-setup.md').read_text())
            self.assertFalse((out / 'resources').exists())
            again = self.eject(client, out, '--draft')
            self.assertNotEqual(again.returncode, 0, 'an existing destination must be refused')
            inside = self.eject(client, client / 'delivery', '--draft')
            self.assertNotEqual(inside.returncode, 0, 'a destination inside the source must be refused')


if __name__ == '__main__':
    unittest.main()
