#!/usr/bin/env python3
"""Short, local-only factory commands. No deployment or paid calls are implicit."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def call(script, *args):
    return subprocess.call([sys.executable, str(ROOT / 'scripts' / script), *args], cwd=ROOT)


def backup(root):
    import site_state
    files = set(site_state.source_inventory(root))
    files.update(p.relative_to(root).as_posix() for p in (root / 'docs').rglob('*') if p.is_file())
    files.update(p.relative_to(root).as_posix() for p in (root / 'schemas').rglob('*') if p.is_file())
    files.update(p.relative_to(root).as_posix() for p in (root / 'evals').rglob('*') if p.is_file())
    files.update(name for name in ('README.md', 'AGENTS.md', 'wf', 'factory-capabilities.json', 'package.json',
                                  'package-lock.json', 'requirements-dev.txt', 'requirements-vertical.txt', 'ruff.toml', '.mcp.json', '.gitignore')
                 if (root / name).is_file())
    files = {name for name in files if not any(part == '.env' or part.startswith('.env.') or part in
             ('.git', '.venv', 'node_modules', '__pycache__') for part in Path(name).parts)}
    target = root / 'reports/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            path = root / name
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root and root in p.parents):
                raise ValueError(f'Backup refuses symlink: {name}')
            archive.write(path, name)
    return target


def restore(archive_path, destination):
    """Validate an archive completely before creating a new, exclusively owned folder."""
    destination = Path(destination).expanduser().absolute()
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [item.filename for item in entries]
        if len(names) != len(set(names)) or sum(item.file_size for item in entries) > 1024**3:
            raise ValueError('Archive contains duplicate entries or exceeds the 1 GB source limit.')
        for item in entries:
            path = Path(item.filename)
            mode = item.external_attr >> 16
            if (path.is_absolute() or '..' in path.parts or '\\' in item.filename or ':' in item.filename
                    or stat.S_ISLNK(mode) or item.is_dir() or not path.parts
                    or any(part in ('.git', '.env', '.venv', 'node_modules') or part.startswith('.env.') for part in path.parts)):
                raise ValueError(f'Unsafe backup entry: {item.filename}')
        destination.mkdir()
        try:
            for item in entries:
                path = destination / item.filename
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, path.open('xb') as target:
                    shutil.copyfileobj(source, target)
                if item.filename == 'wf':
                    path.chmod(0o755)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', default='status',
                        choices=['status', 'new', 'open', 'check', 'backup', 'restore', 'handover', 'approve', 'preview-plan'])
    args, rest = parser.parse_known_args(argv)
    try:
        if args.command == 'new':
            return call('new_site.py', *(rest or ['--guided']))
        if args.command == 'open':
            return call('build.py', '--serve', *rest)
        if args.command == 'handover':
            return call('handover.py', '--build', *rest)
        if args.command == 'preview-plan':
            if len(rest) != 2:
                parser.error('preview-plan needs PLAN_JSON NEW_DESTINATION; your paid draft is reused without another API call')
            return call('factory_run.py', '--plan', rest[0], rest[1], '--serve')
        if args.command == 'check':
            for script, options in [('build.py', []), ('claims.py', ['--strict']), ('contrast.py', [])]:
                code = call(script, *options)
                if code:
                    return code
            return 0
        if args.command == 'backup':
            print(backup(ROOT))
            return 0
        if args.command == 'restore':
            if len(rest) != 2:
                parser.error('restore needs ARCHIVE NEW_DESTINATION')
            print(restore(Path(rest[0]).expanduser(), rest[1]))
            return 0
        import site_state
        state = site_state.readiness(ROOT)
        if args.command == 'approve':
            review_parser = argparse.ArgumentParser(prog='./wf approve', description='Record owner review of the exact current content.')
            review_parser.add_argument('--by', required=True, help='Person who actually reviewed the facts and asset rights')
            review_args = review_parser.parse_args(rest)
            if not review_args.by.strip():
                parser.error('Reviewer must not be empty.')
            if state['open_claims'] or state['placeholders']:
                raise ValueError('Open claims/placeholders remain. Review ./wf status and confirm exact claims before approving.')
            record = dict(version=1, reviewer=review_args.by.strip(), reviewed_at=datetime.now(timezone.utc).isoformat(),
                          fields=state['fields'], scope='rendered-content-and-asset-rights')
            path = ROOT / 'data/content-review.json'
            pending = path.with_suffix('.json.tmp')
            pending.write_text(json.dumps(record, indent=2) + '\n')
            pending.replace(path)
            print('Owner content review recorded. Rebuild to bind it to the output; this does not publish anything.')
            return 0
        receipt, errors = site_state.build_evidence(ROOT, ROOT / 'public')
        output = dict(project=site_state.selected(ROOT)['name'], source=str(ROOT),
                      build_current=not errors, build_problems=errors, release_id=receipt['release_id'] if receipt else None,
                      open_claims=state['open_claims'], placeholders=state['placeholders'],
                      changed_fields=state['changed_fields'], content_review_current=state['content_review_current'],
                      next_action='./wf open' if errors else ('Review the listed content fields' if state['changed_fields'] else './wf handover'))
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f'Cannot complete {args.command}: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
