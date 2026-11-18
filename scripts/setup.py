#!/usr/bin/env python3
"""Install the pinned official Dart Sass and Hugo Extended into this project's ignored .tools folder.

Each tool is skipped when it is already installed there. Hugo is also skipped when the one on
PATH is already the pinned Extended build (CI installs it that way). A private copy keeps a
system upgrade, such as Homebrew moving Hugo forward, from breaking the pinned build.

Every install is also kept in a per-user cache (~/.cache/website-factory, or $XDG_CACHE_HOME), so
setup in the next client copy links the same files instead of downloading them again.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

# SHA-256 of the official release archives for the pinned .sass-version. With a match here,
# setup needs no GitHub API call (and no token or rate limit). A version not listed falls back
# to the digest GitHub's release API publishes. Update both together when bumping the pin.
PINNED = {
    '1.104.1': {
        'linux-x64': '85f31863aa62a1ba93158105609b94206fe9e17a37ad2855a69c543f83d1abae',
        'linux-arm64': '0bc2be53e11bd16462b577d5fe2f4c776287ed371d5aba2f7211cfd385a5c8ed',
        'macos-x64': 'a1c614f4e35641d7a62658beaa1b500962cbf9ac6c568718db4f55505d5490e9',
        'macos-arm64': '1ef58a518ab901c1c4f08890537e111f690c375d984927dafd1decb1c5e6b680',
    },
}

# Official Hugo Extended release files for the pinned .hugo-version, with the SHA-256 digests
# GitHub publishes for them. macOS ships only a universal .pkg; setup unpacks it with pkgutil
# and never runs the installer. Update with .hugo-version and the workflows' hugo-version.
HUGO_PINNED = {
    '0.166.0': {
        'macos': ('hugo_extended_0.166.0_darwin-universal.pkg',
                  '5ac468a54ccd99bd3bfcdacadec25f6fcd6c0606dccfa86bb761d400d3f0a680'),
        'linux-x64': ('hugo_extended_0.166.0_linux-amd64.tar.gz',
                      '0e39b901e3f919f1daae05c8ff64f0c14c8a348ef46886d63f8e6d1bb2653885'),
        'linux-arm64': ('hugo_extended_0.166.0_linux-arm64.tar.gz',
                        '4b282afd8181e5ed182f50f293fc24dd6c42bfa569e555d53bfbc5ee6a1b2982'),
    },
}

def fetch(url):
    headers = {'User-Agent': 'website-starter-setup'}
    # Unauthenticated GitHub API calls are rate-limited per IP, which shared CI runners hit.
    if os.environ.get('GITHUB_TOKEN') and url.startswith('https://api.github.com/'):
        headers['Authorization'] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()

def platform_key():
    system = {'Darwin': 'macos', 'Linux': 'linux'}.get(platform.system())
    machine = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'AMD64': 'x64'}.get(platform.machine())
    if not system or not machine:
        raise SystemExit('Automatic setup supports macOS/Linux arm64/x64. On Windows install the official '
                         'Hugo Extended and standalone Dart Sass on PATH; see README.')
    return system, machine

def checked(payload, expected, what):
    if hashlib.sha256(payload).hexdigest() != expected:
        raise SystemExit(f'{what} download digest mismatch; nothing installed.')
    return payload

def cache_dir():
    return Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'website-factory'

def link_tree(source, destination):
    """Hard-link a tool folder (no extra disk space), copying where a link is not possible."""
    def link(src, dst):
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    shutil.copytree(source, destination, copy_function=link)

def share(installed, name):
    """Keep an installed tool in the per-user cache. Best effort: the cache only saves a download."""
    target = cache_dir() / name
    if target.exists():
        return
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
            link_tree(installed, Path(temporary) / 'tool')
            os.replace(Path(temporary) / 'tool', target)
    except OSError:
        pass

def from_cache(name, destination, works):
    """Install from the per-user cache when it holds a working copy. True when installed."""
    cached = cache_dir() / name
    if not cached.is_dir() or not works(cached):
        return False
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        link_tree(cached, Path(temporary) / 'tool')
        shutil.move(str(Path(temporary) / 'tool'), destination)
    return True

def sass_matches(folder, version):
    try:
        text = subprocess.run([str(folder / 'sass'), '--version'], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return text.split()[:1] == [version]

def install_sass(system, machine):
    version = (ROOT / '.sass-version').read_text().strip()
    destination = ROOT / '.tools/dart-sass'
    shared = f'dart-sass-{version}-{system}-{machine}'
    if destination.exists():
        print(f'Dart Sass: {destination.relative_to(ROOT)} already exists; not overwritten. '
              'Run scripts/build.py to check its version.')
        share(destination, shared)
        return
    if from_cache(shared, destination, lambda folder: sass_matches(folder, version)):
        print(f'Installed Dart Sass {version} from the shared cache (no download).')
        return
    name = f'dart-sass-{version}-{system}-{machine}.tar.gz'
    expected = PINNED.get(version, {}).get(f'{system}-{machine}')
    if expected:
        url = f'https://github.com/sass/dart-sass/releases/download/{version}/{name}'
    else:
        release = json.loads(fetch(f'https://api.github.com/repos/sass/dart-sass/releases/tags/{version}'))
        asset = next(a for a in release['assets'] if a['name'] == name)
        digest = asset.get('digest', '')
        if not digest.startswith('sha256:'):
            raise SystemExit('Official release has no SHA-256 digest. Install manually; automatic setup stopped.')
        expected, url = digest.split(':', 1)[1], asset['browser_download_url']
    payload = checked(fetch(url), expected, 'Compiler')
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        root = Path(temporary)
        with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
            for member in archive.getmembers():
                target = (root / member.name).resolve()
                if root.resolve() not in target.parents or not (member.isdir() or member.isfile()):
                    raise SystemExit('Unsafe compiler archive entry; nothing installed.')
            archive.extractall(root, filter='data')  # the checks above, plus the stdlib's own refusal of links and devices
        shutil.move(str(root / 'dart-sass'), destination)
    share(destination, shared)
    print(f'Installed Dart Sass {version}.')

def hugo_matches(executable, version):
    """True when this executable is the Extended build of the pinned version."""
    from doctor import hugo_ok
    try:
        text = subprocess.run([str(executable), 'version'], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return hugo_ok(text, version)

def hugo_binary(payload, name, work):
    """Return the hugo executable unpacked from an official release file into work."""
    if name.endswith('.tar.gz'):
        with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
            member = next((m for m in archive.getmembers() if m.name.lstrip('./') == 'hugo'), None)
            if member is None or not member.isfile():
                raise SystemExit('Hugo archive has no plain hugo file; nothing installed.')
            (work / 'hugo').write_bytes(archive.extractfile(member).read())
        return work / 'hugo'
    package = work / name
    package.write_bytes(payload)
    expanded = work / 'expanded'
    # --expand-full unpacks the payload; it runs no installer scripts.
    subprocess.run(['pkgutil', '--expand-full', str(package), str(expanded)], check=True, capture_output=True)
    found = [p for p in expanded.rglob('hugo') if p.is_file() and not p.is_symlink()]
    if len(found) != 1:
        raise SystemExit('Hugo package did not contain exactly one hugo file; nothing installed.')
    return found[0]

def install_hugo(system, machine):
    version = (ROOT / '.hugo-version').read_text().strip()
    destination = ROOT / '.tools/hugo'
    shared = f'hugo-{version}-{system}-{machine}'
    if destination.exists():
        print(f'Hugo: {destination.relative_to(ROOT)} already exists; not overwritten. '
              'Delete it and run setup again to reinstall.')
        share(destination, shared)
        return
    on_path = shutil.which('hugo')
    if on_path and hugo_matches(on_path, version):
        print(f'Hugo: {on_path} is already Extended {version}; nothing to install.')
        return
    if from_cache(shared, destination, lambda folder: hugo_matches(folder / 'hugo', version)):
        print(f'Installed Hugo Extended {version} in {destination.relative_to(ROOT)} from the shared cache (no download).')
        return
    release = HUGO_PINNED.get(version, {})
    name, expected = release.get('macos' if system == 'macos' else f'{system}-{machine}', (None, None))
    if not name:
        raise SystemExit(f'No pinned Hugo {version} download for {system}-{machine}. Add it to HUGO_PINNED '
                         f'or install Hugo Extended {version} on PATH yourself.')
    payload = checked(fetch(f'https://github.com/gohugoio/hugo/releases/download/v{version}/{name}'),
                      expected, 'Hugo')
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        work = Path(temporary)
        binary = hugo_binary(payload, name, work)
        binary.chmod(0o755)
        if not hugo_matches(binary, version):
            raise SystemExit(f'The unpacked hugo does not report Extended {version}; nothing installed.')
        (work / 'bin').mkdir()
        shutil.move(str(binary), work / 'bin/hugo')
        shutil.move(str(work / 'bin'), destination)
    share(destination, shared)
    print(f'Installed Hugo Extended {version} in {destination.relative_to(ROOT)}.')

def main():
    system, machine = platform_key()
    install_sass(system, machine)
    install_hugo(system, machine)
    print('Next: python3 scripts/doctor.py, then python3 scripts/build.py.')

if __name__ == '__main__':
    main()
