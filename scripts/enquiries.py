#!/usr/bin/env python3
"""Read contact-form enquiries stored in the live ENQUIRY KV namespace.

  python3 scripts/enquiries.py list                     # newest first, one line each
  python3 scripts/enquiries.py export --format csv -o enquiries.csv
  python3 scripts/enquiries.py export --format json
  python3 scripts/enquiries.py delete --email person@example.com   # a visitor's deletion request
  python3 scripts/enquiries.py summary                  # counts by month and type; no names or addresses

Runs Cloudflare's wrangler against this project's wrangler.toml, so log in first with
`npx wrangler login`. Only keys starting with "enquiry:" are read; rate-limit counters are
skipped. list and export only read. delete shows every enquiry sent from that address and
removes them only after you type "delete" (or pass --yes); it cannot be undone. Exports
contain personal data, so keep them out of the repository and delete them when you are done.
"""
import argparse
from collections import Counter
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

def keyed_enquiries():
    """(KV key, enquiry) pairs, newest first."""
    keys = json_from(wrangler('list', '--prefix', 'enquiry:'), '[')
    found, failed = [], []
    for key in keys:
        try:
            found.append((key['name'], json_from(wrangler('get', key['name']), '{')))
        except (SystemExit, ValueError, KeyError) as error:
            failed.append(key.get('name', '?'))
            print(f"Could not read {key.get('name', '?')}: {error}", file=sys.stderr)
    if failed:
        raise SystemExit(f'Incomplete enquiry read: {len(failed)} of {len(keys)} records failed. No export was written; retry after resolving the read failure.')
    return sorted(found, key=lambda pair: pair[1].get('received', ''), reverse=True)

def enquiries():
    return [enquiry for _, enquiry in keyed_enquiries()]

def summary(e):
    return f"{e.get('received', '?')[:16]}  {e.get('name', '')} <{e.get('email', '')}>  {e.get('project-type', '')}"

def monthly(found):
    """Counts by month and by project type, with no names or addresses, so it can go in a report."""
    months = Counter((e.get('received') or '')[:7] or 'unknown' for e in found)
    kinds = Counter(e.get('project-type') or 'not given' for e in found)
    lines = ['Enquiries by month (stored enquiries expire after 90 days, so this covers about three months):']
    lines += [f'  {month}  {count}' for month, count in sorted(months.items())] or ['  none']
    lines += ['By project type:'] + [f'  {count:>3}  {kind}' for kind, count in kinds.most_common()]
    return '\n'.join(lines)

def delete(email, confirm=input):
    """Delete every stored enquiry from this address after confirmation. Returns the exit status."""
    wanted = email.strip().lower()
    matches = [(key, e) for key, e in keyed_enquiries() if str(e.get('email', '')).strip().lower() == wanted]
    if not matches:
        print(f'No stored enquiries from {email.strip()}. Nothing was deleted.')
        return 0
    for _, e in matches:
        print(summary(e))
    if confirm:
        try:
            answer = confirm(f'Delete these {len(matches)} enquiries? This cannot be undone. Type "delete" to confirm: ')
        except EOFError:  # no one at the keyboard
            answer = ''
        if answer.strip().lower() != 'delete':
            print('\nCancelled. Nothing was deleted.')
            return 1
    for done, (key, _) in enumerate(matches):
        try:
            wrangler('delete', key)
        except SystemExit as error:
            raise SystemExit(f'Deleted {done} of {len(matches)} before a failure; run delete again for the rest.\n{error}')
    print(f'Deleted {len(matches)} enquiries from {email.strip()}. Also delete any copy in your notification '
          'service and mailbox, then tell the person it is done.')
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='Show one line per enquiry, newest first')
    export = sub.add_parser('export', help='Write every enquiry as JSON or CSV')
    export.add_argument('--format', choices=['json', 'csv'], default='json')
    export.add_argument('-o', '--output', help='File to write (default: print to the screen)')
    sub.add_parser('summary', help='Counts by month and project type, with no personal data')
    remove = sub.add_parser('delete', help='Delete every stored enquiry sent from one email address')
    remove.add_argument('--email', required=True, help='The address the person used on the form')
    remove.add_argument('--yes', action='store_true', help='Skip the confirmation question')
    args = parser.parse_args(argv)

    if args.command == 'delete':
        return delete(args.email, confirm=None if args.yes else input)
    found = enquiries()
    if args.command == 'summary':
        print(monthly(found))
        return 0
    if args.command == 'list':
        if not found:
            print('No stored enquiries.')
        for e in found:
            print(summary(e))
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
