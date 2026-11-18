#!/usr/bin/env python3
"""Pinned Hugo install: verified digest, a single plain binary, no overwrite, and a shared cache. Uses no network."""
import hashlib
import io
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest import mock

import setup

FAKE = b'#!/bin/sh\necho "hugo v9.9.9-0123abc+extended linux/amd64"\n'

def archive(members):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()

class HugoInstall(unittest.TestCase):
    def temp(self):
        path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def setUp(self):
        # Never touch the real per-user cache.
        cache = self.temp()
        patcher = mock.patch.object(setup, 'cache_dir', return_value=cache)
        patcher.start()
        self.addCleanup(patcher.stop)

    def install(self, payload, digest=None, root=None, fetch=None):
        root = root or self.temp()
        (root / '.hugo-version').write_text('9.9.9\n')
        pinned = {'9.9.9': {'linux-x64': ('hugo_extended_9.9.9_linux-amd64.tar.gz',
                                          digest or hashlib.sha256(payload).hexdigest())}}
        with mock.patch.object(setup, 'ROOT', root), mock.patch.object(setup, 'HUGO_PINNED', pinned), \
                mock.patch.object(setup, 'fetch', fetch or mock.Mock(return_value=payload)), \
                mock.patch('shutil.which', return_value=None):
            setup.install_hugo('linux', 'x64')
        return root

    def test_installs_the_checked_binary(self):
        root = self.install(archive({'hugo': FAKE, 'LICENSE': b'x'}))
        self.assertEqual((root / '.tools/hugo/hugo').read_bytes(), FAKE)
        self.assertEqual(list((root / '.tools/hugo').iterdir()), [root / '.tools/hugo/hugo'], 'only the binary is kept')

    def test_digest_mismatch_installs_nothing(self):
        root = self.temp()
        with self.assertRaises(SystemExit):
            self.install(archive({'hugo': FAKE}), digest='0' * 64, root=root)
        self.assertFalse((root / '.tools/hugo').exists())

    def test_archive_without_hugo_is_refused(self):
        with self.assertRaises(SystemExit):
            self.install(archive({'README.md': b'x'}))

    def test_next_project_installs_from_the_cache(self):
        self.install(archive({'hugo': FAKE}))
        offline = mock.Mock(side_effect=AssertionError('no download when the cache has it'))
        second = self.install(archive({'hugo': FAKE}), fetch=offline)
        self.assertEqual((second / '.tools/hugo/hugo').read_bytes(), FAKE)
        offline.assert_not_called()

    def test_existing_install_is_kept(self):
        root = self.install(archive({'hugo': FAKE}))
        (root / '.tools/hugo/hugo').write_bytes(b'mine')
        with mock.patch.object(setup, 'ROOT', root), mock.patch.object(setup, 'fetch') as fetch:
            setup.install_hugo('linux', 'x64')
        fetch.assert_not_called()
        self.assertEqual((root / '.tools/hugo/hugo').read_bytes(), b'mine')

if __name__ == '__main__':
    unittest.main()
