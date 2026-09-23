#!/usr/bin/env python3
"""Install pinned official Dart Sass into this project's ignored .tools folder."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import tarfile
import tempfile
import urllib.request
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

def fetch(url):
    headers = {'User-Agent': 'website-starter-setup'}
    # Unauthenticated GitHub API calls are rate-limited per IP, which shared CI runners hit.
    if os.environ.get('GITHUB_TOKEN') and url.startswith('https://api.github.com/'):
        headers['Authorization'] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()

def main():
    system = {'Darwin': 'macos', 'Linux': 'linux'}.get(platform.system())
    machine = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'AMD64': 'x64'}.get(platform.machine())
    if not system or not machine:
        raise SystemExit('Automatic setup supports macOS/Linux arm64/x64. On Windows install the official standalone compiler on PATH; see README.')
    version = (ROOT / '.sass-version').read_text().strip()
    destination = ROOT / '.tools/dart-sass'
    if destination.exists():
        raise SystemExit('Local Dart Sass already exists. Run scripts/build.py to check its version; setup does not overwrite it.')
    name = f'dart-sass-{version}-{system}-{machine}.tar.gz'
    release = json.loads(fetch(f'https://api.github.com/repos/sass/dart-sass/releases/tags/{version}'))
    asset = next(a for a in release['assets'] if a['name'] == name)
    digest = asset.get('digest', '')
    if not digest.startswith('sha256:'):
        raise SystemExit('Official release has no SHA-256 digest. Install manually; automatic setup stopped.')
    payload = fetch(asset['browser_download_url'])
    if hashlib.sha256(payload).hexdigest() != digest.split(':', 1)[1]:
        raise SystemExit('Compiler download digest mismatch; nothing installed.')
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        root = Path(temporary)
        with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
            for member in archive.getmembers():
                target = (root / member.name).resolve()
                if root.resolve() not in target.parents or not (member.isdir() or member.isfile()):
                    raise SystemExit('Unsafe compiler archive entry; nothing installed.')
            archive.extractall(root)
        shutil.move(str(root / 'dart-sass'), destination)
    print(f'Installed Dart Sass {version}. Install Hugo Extended {(ROOT / ".hugo-version").read_text().strip()} separately, then run python3 scripts/build.py.')

if __name__ == '__main__':
    main()
