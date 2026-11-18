#!/usr/bin/env python3
"""Care check: smoke.py options pass through, the extra checks flag real problems, and a down site fails."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import socket
import tempfile
import threading
import unittest

import care

def local_site(test):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200 if self.path == '/' else 404)
            self.end_headers()
            self.wfile.write(b'<html><meta name="robots" content="noindex"></html>')

        def do_POST(self):
            raise AssertionError('the care check must never POST')

        def log_message(self, *args):
            pass
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    test.addCleanup(httpd.server_close)
    test.addCleanup(httpd.shutdown)
    return f'http://127.0.0.1:{httpd.server_port}'

def closed_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

class CareCheck(unittest.TestCase):
    def test_smoke_options_pass_through(self):
        results = care.check_line(local_site(self) + ' --noindex --no-endpoint')
        failed = [what for status, what, _ in results if status == 'FAIL']
        passed = [what for status, what, _ in results if status == 'ok']
        self.assertIn('security headers present', failed, 'smoke.py checks run')
        self.assertIn('search engines kept out (preview)', passed, '--noindex reached smoke.py')
        self.assertTrue(any(what.startswith('home page loads in') for what in passed), 'care checks run')

    def test_https_extras(self):
        original = care.smoke.fetch
        care.smoke.fetch = lambda url: (200, {}, '')
        self.addCleanup(setattr, care.smoke, 'fetch', original)
        def run(days, redirect):
            return {what: status for status, what, _ in
                    care.care_checks('https://client.example', cert=lambda host, port: days, redirect=lambda host: redirect)}
        results = run(5, (200, ''))
        self.assertEqual(results['certificate valid for 5 more days'], 'WARN')
        self.assertEqual(results['http:// sends visitors to https://'], 'WARN', 'http answering 200 is an insecure copy')
        self.assertEqual(set(run(60, (301, 'https://client.example/')).values()), {'ok'})

    def test_down_site_fails(self):
        text, failed = care.report([f'http://127.0.0.1:{closed_port()}'])
        self.assertTrue(failed)
        self.assertIn('**FAIL** site did not answer', text)

    def test_bad_line_fails_plainly(self):
        self.assertEqual(care.check_line('https://x.example --form sideways')[0][0], 'FAIL')

    def test_site_list_skips_notes(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        (folder / 'care-sites.txt').write_text('# clients\nhttps://a.example --form on  # studio\n\nhttps://b.example\n')
        self.assertEqual(care.read_sites(folder / 'care-sites.txt'), ['https://a.example --form on', 'https://b.example'])

if __name__ == '__main__':
    unittest.main()
