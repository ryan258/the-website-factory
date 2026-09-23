#!/usr/bin/env python3
"""Read contact-form enquiries stored in the live ENQUIRY KV namespace.

  python3 scripts/enquiries.py list                     # newest first, one line each
  python3 scripts/enquiries.py export --format csv -o enquiries.csv
  python3 scripts/enquiries.py export --format json

Runs Cloudflare's wrangler against this project's wrangler.toml, so log in first with
`npx wrangler login`. Only keys starting with "enquiry:" are read; rate-limit counters are
skipped. Read-only: nothing is changed or deleted. Exports contain personal data, so keep
them out of the repository and delete them when you are done.
"""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# Same pin as scripts/check_contact.sh. WRANGLER overrides it (the tests use a stand-in).
WRANGLER = os.environ.get('WRANGLER', 'npx --yes wrangler@4.136.2')
FIELDS = ['received', 'name', 'email', 'company', 'project-type', 'budget', 'message']

def wrangler(*args):
    result = subprocess.run([*shlex.split(WRANGLER), 'kv', 'key', *args, '--binding', 'ENQUIRY', '--remote'],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'wrangler failed ({result.returncode}). Are you logged in? Try: npx wrangler login\n{result.stderr.strip()}')
    return result.stdout

def json_from(output, opener):
    """wrangler can print notices before its answer; read from the first JSON bracket."""
    start = output.find(opener)
    if start < 0:
        raise SystemExit(f'Unexpected wrangler output:\n{output.strip()[:500]}')
    return json.JSONDecoder().raw_decode(output[start:])[0]

def enquiries():
    keys = json_from(wrangler('list', '--prefix', 'enquiry:'), '[')
    found = []
    for key in keys:
        try:
            found.append(json_from(wrangler('get', key['name']), '{'))
        except SystemExit as error:
            print(f"Skipped {key['name']}: {error}", file=sys.stderr)
    return sorted(found, key=lambda e: e.get('received', ''), reverse=True)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='Show one line per enquiry, newest first')
    export = sub.add_parser('export', help='Write every enquiry as JSON or CSV')
    export.add_argument('--format', choices=['json', 'csv'], default='json')
    export.add_argument('-o', '--output', help='File to write (default: print to the screen)')
    args = parser.parse_args(argv)

    found = enquiries()
    if args.command == 'list':
        if not found:
            print('No stored enquiries.')
        for e in found:
            print(f"{e.get('received', '?')[:16]}  {e.get('name', '')} <{e.get('email', '')}>  {e.get('project-type', '')}")
        print(f'{len(found)} enquiries. Stored enquiries are deleted automatically after 90 days.', file=sys.stderr)
        return 0
    if args.format == 'json':
        text = json.dumps(found, indent=2, ensure_ascii=False) + '\n'
    else:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=FIELDS, extrasaction='ignore')
        writer.writeheader()
        # Visitors write these fields. A cell starting with = + - @ would run as a spreadsheet
        # formula, so it is prefixed with ' to open as plain text.
        safe = lambda value: "'" + value if isinstance(value, str) and value[:1] in ('=', '+', '-', '@', '\t', '\r') else value
        writer.writerows({k: safe(v) for k, v in e.items()} for e in found)
        text = buffer.getvalue()
    if args.output:
        Path(args.output).write_text(text)
        print(f'Wrote {len(found)} enquiries to {args.output}. It contains personal data; delete it when done.', file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0

if __name__ == '__main__':
    sys.exit(main())
