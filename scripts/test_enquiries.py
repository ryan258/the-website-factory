#!/usr/bin/env python3
"""scripts/enquiries.py against a stand-in wrangler: no account, no network."""
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STORE = {
    'enquiry:2026-09-01T10:00:00.000Z:a': {'name': 'Older Person', 'email': 'old@example.com', 'company': '',
        'project-type': 'Landing pages', 'budget': 'Not sure yet', 'message': 'Hi', 'received': '2026-09-01T10:00:00.000Z'},
    'enquiry:2026-09-20T10:00:00.000Z:b': {'name': 'New Person', 'email': 'new@example.com', 'company': 'Acme',
        'project-type': 'Speed audits', 'budget': 'Under $2,400', 'message': '=HYPERLINK("http://x.invalid")',
        'received': '2026-09-20T10:00:00.000Z'},
}
# Stands in for `wrangler kv key list|get ... --binding ENQUIRY --remote`, including the notice
# line real wrangler can print before its answer.
FAKE = f'''import json, os, sys
store = {json.dumps(STORE)}
args = sys.argv[1:]
assert args[:2] == ['kv', 'key'] and '--remote' in args and args[args.index('--binding') + 1] == 'ENQUIRY', args
print('Resource location: remote')
if args[2] == 'list':
    prefix = args[args.index('--prefix') + 1]
    keys = sorted(store) + ['ratelimit:abc']
    print(json.dumps([{{'name': k}} for k in keys if k.startswith(prefix)]))
elif args[2] == 'get':
    print(json.dumps(store[args[3]]))
elif args[2] == 'delete':
    with open(os.environ['DELETED'], 'a') as log:
        log.write(args[3] + '\\n')
'''

class EnquiriesTests(unittest.TestCase):
    def run_script(self, *args, fake=FAKE, answer=''):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / 'wrangler.py'
            script.write_text(fake)
            deleted = Path(tmp) / 'deleted.txt'
            env = dict(os.environ, WRANGLER=f'{sys.executable} {script}', DELETED=str(deleted))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/enquiries.py'), *args],
                                    env=env, capture_output=True, text=True, input=answer)
            result.deleted = deleted.read_text().split() if deleted.exists() else []
            return result

    def test_list_is_newest_first_and_skips_rate_limit_keys(self):
        result = self.run_script('list')
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn('New Person', lines[0])
        self.assertIn('Older Person', lines[1])

    def test_json_export_has_every_field(self):
        result = self.run_script('export', '--format', 'json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({e['email'] for e in json.loads(result.stdout)}, {'old@example.com', 'new@example.com'})

    def test_csv_export_neutralizes_formulas(self):
        result = self.run_script('export', '--format', 'csv')
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = list(csv.DictReader(io.StringIO(result.stdout)))
        self.assertEqual(rows[0]['name'], 'New Person')
        self.assertTrue(rows[0]['message'].startswith("'="), rows[0]['message'])

    def test_delete_removes_only_that_address_after_confirmation(self):
        result = self.run_script('delete', '--email', ' NEW@example.com ', answer='delete\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.deleted, ['enquiry:2026-09-20T10:00:00.000Z:b'])
        self.assertIn('New Person', result.stdout, 'what will be deleted is shown first')

    def test_delete_without_confirmation_deletes_nothing(self):
        for answer in ('', 'y\n', 'yes\n'):
            result = self.run_script('delete', '--email', 'new@example.com', answer=answer)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.deleted, [], answer)
            self.assertIn('Nothing was deleted', result.stdout)

    def test_delete_with_yes_and_unknown_address(self):
        self.assertEqual(self.run_script('delete', '--email', 'old@example.com', '--yes').deleted,
                         ['enquiry:2026-09-01T10:00:00.000Z:a'])
        result = self.run_script('delete', '--email', 'nobody@example.com', '--yes')
        self.assertEqual((result.returncode, result.deleted), (0, []))

    def test_summary_counts_without_personal_data(self):
        result = self.run_script('summary')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('2026-09  2', result.stdout)
        self.assertIn('1  Speed audits', result.stdout)
        for private in ('Person', '@example.com', 'HYPERLINK'):
            self.assertNotIn(private, result.stdout)

    def test_wrangler_failure_is_reported(self):
        result = self.run_script('list', fake='import sys; sys.exit(3)')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('wrangler login', result.stderr)

if __name__ == '__main__':
    unittest.main()
