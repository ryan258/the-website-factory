#!/usr/bin/env python3
"""Build from any cwd using system tools or the project's private Dart Sass."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import json
import hashlib
from factory import validate

ROOT = Path(__file__).resolve().parents[1]

def environment():
    env = os.environ.copy()
    local = ROOT / '.tools/dart-sass'
    if local.is_dir():
        env['PATH'] = str(local) + os.pathsep + env.get('PATH', '')
    env.setdefault('HUGO_CACHEDIR', str(Path(tempfile.gettempdir()) / 'website-starter-hugo-cache'))
    return env


def publish_output(source, destination):
    """Reconcile owned output without deleting unknown or owner-modified files."""
    manifest = destination / '.factory-build.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    current = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in source.rglob('*') if p.is_file()}
    stale = set(previous) - set(current)
    for name in previous:
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Invalid output manifest path.')
    for name in set(current) | stale:
        path = destination / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != destination.parent):
            raise ValueError(f'Refusing symlink in generated output: {name}')
    for name in stale:
        path = destination / name
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != previous[name]:
            raise ValueError(f'Previously generated file was edited: {name}. Choose an empty destination.')
    if destination.exists():
        for path in destination.rglob('*.html'):
            name = path.relative_to(destination).as_posix()
            if name not in current and name not in previous:
                raise ValueError(f'Untracked HTML would remain: {name}. Choose an empty destination.')
    destination.mkdir(parents=True, exist_ok=True)
    for name in stale:
        (destination / name).unlink(missing_ok=True)
    for name in current:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, path)
    manifest.write_text(json.dumps(current, indent=2)+'\n')

def content_selection(destination):
    config = json.loads((ROOT/'data/factory.json').read_text())
    profile = json.loads((ROOT/'data/presets'/f"{config['preset']}.json").read_text())
    shutil.copytree(ROOT/'content', destination)
    for path in destination.iterdir():
        if path.is_dir() and path.name not in profile['pages']:
            if path.name != 'site-kit' or not config['workshop']:
                shutil.rmtree(path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', default='public')
    parser.add_argument('--base-url')
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--port', type=int, default=1313)
    args = parser.parse_args()
    errors = validate(ROOT)
    if errors:
        parser.error("Invalid factory configuration:\n" + "\n".join(errors))
    env = environment()
    for binary, pin in [('hugo', '.hugo-version'), ('sass', '.sass-version')]:
        exe = shutil.which(binary, path=env['PATH'])
        if not exe:
            parser.error(f'{binary} is missing. See README.md; run scripts/setup.py for Dart Sass.')
        command = [exe, 'version' if binary == 'hugo' else '--version']
        result = subprocess.run(command, env=env, cwd=ROOT, capture_output=True, text=True)
        version = (ROOT / pin).read_text().strip()
        if result.returncode or not re.search(r'(?<![\d.])' + re.escape(version) + r'(?![\d.])', result.stdout):
            parser.error(f'{binary}: expected {version}; found {result.stdout.strip() or result.stderr.strip()}')
        if binary == 'hugo' and '+extended' not in result.stdout:
            parser.error('Hugo Extended is required.')
    cmd = ['hugo', '--minify', '--gc']
    if args.base_url:
        cmd += ['--baseURL', args.base_url]
    destination = (ROOT/args.destination).absolute()
    resolved = destination.resolve()
    if resolved == ROOT or resolved in ROOT.parents or any(resolved == ROOT/x or ROOT/x in resolved.parents for x in ('assets','content','data','layouts','static','scripts','docs','node_modules','.tools')):
        parser.error('Destination must be a build directory, never a source or parent directory.')
    try:
        with tempfile.TemporaryDirectory(prefix='factory-build-') as temporary:
            temporary = Path(temporary)
            content_selection(temporary/'content')
            output = temporary/'output'
            result = subprocess.run(cmd + ['--contentDir',str(temporary/'content'),'--destination',str(output)], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode or re.search(r'(?m)^WARN\b', result.stdout):
                print(result.stdout, file=sys.stderr)
                return result.returncode or 1
            from check_site import check
            errors = check(output.resolve())
            if errors:
                print('\n'.join(errors),file=sys.stderr)
                return 1
            publish_output(output, destination)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f'Build and generated-output checks passed: {args.destination}')
    if args.serve:
        from functools import partial
        from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
        handler = partial(SimpleHTTPRequestHandler, directory=str(destination))
        with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
            print(f'Preview: http://127.0.0.1:{args.port}/ — serving verified output; rebuild after edits.', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    return 0

if __name__ == '__main__':
    sys.exit(main())
