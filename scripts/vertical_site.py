#!/usr/bin/env python3
"""Create a client from a specialist vertical through the shared factory."""
import argparse
from pathlib import Path
import subprocess
import importlib.util
import shutil
import tempfile
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERTICALS = {"contractor": "jones-construction", "restaurant": "hot-eats"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vertical", choices=VERTICALS)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--preset", default="diner", help="Restaurant preset")
    parser.add_argument("--specialty", default="septic", choices=["septic", "excavation"])
    args = parser.parse_args()
    adapter = ROOT.parent / VERTICALS[args.vertical] / "scripts" / "sculpt.py"
    if not adapter.is_file():
        parser.error(f"Vertical source is required: {adapter.parent.parent}")
    destination = args.destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink() or not destination.parent.is_dir():
        parser.error('Destination must not exist, and its parent must already exist.')
    if destination.resolve() == ROOT or ROOT in destination.resolve().parents:
        parser.error('Choose a destination outside the factory.')
    if not args.name.strip() or len(args.name) > 60 or any(ord(c) < 32 for c in args.name):
        parser.error('Name must be 1–60 characters without control characters.')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.slug):
        parser.error('Use a lowercase hyphenated slug.')
    if args.vertical == 'contractor' and importlib.util.find_spec('yaml') is None:
        parser.error('Contractor adapter requires PyYAML in this interpreter. Run: python3 -m pip install -r requirements-vertical.txt')
    if args.vertical == 'restaurant' and (not re.fullmatch(r'[a-z0-9-]+', args.preset)
            or not (adapter.parents[1] / 'presets' / f'{args.preset}.toml').is_file()):
        parser.error('Choose a restaurant preset present in the vertical master.')
    # Complete neutralization in a disposable sibling before reserving the real target.
    with tempfile.TemporaryDirectory(prefix='.factory-vertical-', dir=destination.parent) as temporary:
        staged = Path(temporary) / 'client'
        command = [sys.executable, str(adapter), "--destination", str(staged),
               "--name", args.name, "--slug", args.slug]
        command += ["--preset", args.preset] if args.vertical == "restaurant" else ["--specialty", args.specialty]
        result = subprocess.run(command, cwd=adapter.parents[1])
        if result.returncode:
            return result.returncode
        receipt = staged / 'scripts/scaffold-origin.json'
        if not receipt.is_file() or json.loads(receipt.read_text()).get('contract_version') != 1:
            parser.error('Vertical adapter did not produce a supported scaffold receipt.')
        destination.mkdir()  # Exclusive reservation; never remove a pre-existing path.
        try:
            shutil.copytree(staged, destination, dirs_exist_ok=True)
        except BaseException:
            shutil.rmtree(destination)
            raise
    print(f'Created {destination}. Read its client start guide; build and review are still pending.')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
