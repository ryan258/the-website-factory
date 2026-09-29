#!/usr/bin/env python3
"""Run the fast quality gates the way CI sees the project.

  python3 scripts/verify.py          # on a clean copy: what a commit would contain, without ignored files
  python3 scripts/verify.py --here   # in this folder, on the last build (CI uses this)

A test that reads a gitignored file, or a script that needs a package only this machine has, passes in
the working folder and fails in CI. The default copies the files git tracks or would add (so uncommitted
edits count, .gitignore'd files do not) to a temporary folder, links the installed tools, builds, and runs
the gates there. Nothing is staged or changed here. Browser checks and the Pages contact test are left to CI.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = [['python3', 'scripts/build.py']]
# The one list of gates. CI runs it too, so what passes here is what CI runs.
GATES = [
    ['python3', 'scripts/check_site.py', 'public'],
    ['npm', 'test'],
    ['python3', 'scripts/schemas.py', '--check'],
    ['python3', 'scripts/claims.py', '--strict'],
    ['python3', 'scripts/contrast.py'],
    ['npm', 'run', '-s', 'lint'],
]

def run_all(commands, folder):
    for command in commands:
        print('$', ' '.join(command), flush=True)
        if subprocess.run(command, cwd=folder).returncode:
            print(f'\nFAILED: {" ".join(command)}', file=sys.stderr)
            return 1
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--here', action='store_true', help='Run the gates in this folder instead of a clean copy')
    if parser.parse_args(argv).here:
        return run_all(GATES, ROOT)
    try:
        listed = subprocess.run(['git', 'ls-files', '-z', '-co', '--exclude-standard'], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.split('\0')
    except (OSError, subprocess.CalledProcessError):
        print('The clean-copy check needs a git repository. Use --here to run the gates in place.', file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix='factory-verify-') as tmp:
        copy = Path(tmp)
        for name in filter(None, listed):
            source = ROOT / name
            if source.is_file():  # a tracked file deleted in the working folder is skipped, as a commit would
                (copy / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, copy / name)
        for installed in ('node_modules', '.tools'):
            if (ROOT / installed).exists():
                (copy / installed).symlink_to(ROOT / installed)
        status = run_all(BUILD + GATES, copy)
    print('Clean-copy gates passed.' if not status else 'Clean-copy gates FAILED.')
    return status

if __name__ == '__main__':
    sys.exit(main())
