#!/usr/bin/env python3
"""AI drafting and the one-command run, against a local stand-in for the Messages API.

No network and no API key: ANTHROPIC_BASE_URL points the real Anthropic SDK at a tiny
local server that records each request and answers with a recorded draft.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import draft_plan  # noqa: E402
import factory_run  # noqa: E402

RECORDED = (ROOT / 'evals/recorded/bakery.json').read_text()

class FakeAPI(BaseHTTPRequestHandler):
    requests, reply = [], {}
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['content-length'])))
        FakeAPI.requests.append(dict(path=self.path, headers=dict(self.headers), body=body))
        payload = json.dumps(FakeAPI.reply).encode()
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.send_header('content-length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *args):
        pass

def message(text, stop='end_turn'):
    return {'id': 'msg_test', 'type': 'message', 'role': 'assistant', 'model': draft_plan.MODEL,
            'content': [{'type': 'text', 'text': text}] if text else [], 'stop_reason': stop,
            'stop_sequence': None, 'usage': {'input_tokens': 10, 'output_tokens': 10}}

class AITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FakeAPI)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.env = {'ANTHROPIC_BASE_URL': f'http://127.0.0.1:{cls.server.server_address[1]}', 'ANTHROPIC_API_KEY': 'test-key'}
        cls.saved = {k: os.environ.get(k) for k in cls.env}
        os.environ.update(cls.env)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        for key, value in cls.saved.items():
            os.environ.pop(key, None) if value is None else os.environ.__setitem__(key, value)

    def setUp(self):
        FakeAPI.requests.clear()
        FakeAPI.reply = message(RECORDED)

    def test_request_uses_structured_output_and_fallbacks(self):
        result = draft_plan.draft('A bakery brief.', source='bakery.md')
        sent = FakeAPI.requests[0]
        body = sent['body']
        self.assertEqual(body['model'], 'claude-opus-5')
        self.assertEqual(body['fallbacks'], 'default')
        self.assertIn('server-side-fallback-2026-07-01', sent['headers'].get('anthropic-beta', ''))
        self.assertEqual(body['output_config']['format']['type'], 'json_schema')
        self.assertEqual(body['thinking'], {'type': 'adaptive'})
        self.assertIn('To be confirmed', body['system'])
        project = result['projects'][0]
        self.assertEqual(project['name'], 'Rise & Crumb Bakery')
        self.assertEqual([p['name'] for p in project['pages']], ['Home', 'Cakes', 'Contact'])
        self.assertEqual(project['pages'][0]['sections'][0]['kind'], 'Introduction', 'planner labels, not module keys')
        self.assertTrue(all(s['state'] == 'draft' for p in project['pages'] for s in p['sections']))

    def test_refusal_and_truncation_fail_plainly(self):
        FakeAPI.reply = message('', stop='refusal')
        with self.assertRaisesRegex(SystemExit, 'declined'):
            draft_plan.draft('brief')
        FakeAPI.reply = message('{"name": "cut', stop='max_tokens')
        with self.assertRaisesRegex(SystemExit, 'cut off'):
            draft_plan.draft('brief')

    def test_off_schema_answer_is_rejected(self):
        FakeAPI.reply = message(json.dumps({'name': 'X'}))
        with self.assertRaisesRegex(SystemExit, 'plan format'):
            draft_plan.draft('brief')

    def test_brief_to_checked_client_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / 'bakery.md'
            brief.write_text((ROOT / 'evals/briefs/bakery.md').read_text())
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/factory_run.py'), str(brief), str(Path(tmp) / 'site')],
                                    capture_output=True, text=True, env={**os.environ, **self.env})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            dest = Path(tmp) / 'site'
            self.assertEqual(json.loads((dest / 'data/factory.json').read_text())['preset'], 'rise-crumb-bakery')
            self.assertEqual([p.name for p in (dest / 'data/presets').iterdir()], ['rise-crumb-bakery.json'])
            home = (dest / 'public/index.html').read_text()
            self.assertIn('Rise & Crumb Bakery', home)
            self.assertIn('href=/cakes/>', home, 'every page is in the menu')
            self.assertIn('noindex', home)
            self.assertTrue((dest / 'public/cakes/index.html').is_file())
            reviewed = (dest / 'docs/plan-review.md').read_text()
            self.assertIn('opening hours', reviewed)
            self.assertEqual(factory_run.BASE, 'consultant')
            self.assertFalse((ROOT / 'data/presets/rise-crumb-bakery.json').exists(), 'the master must not change')

if __name__ == '__main__':
    unittest.main()
