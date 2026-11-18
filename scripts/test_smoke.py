#!/usr/bin/env python3
"""scripts/smoke.py against local stand-in servers: a healthy release, and the stale build it must catch."""
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import re
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke  # noqa: E402

SECURE = {'Content-Security-Policy': "default-src 'self'; frame-ancestors 'none'", 'Strict-Transport-Security': 'max-age=1',
          'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer',
          'Permissions-Policy': 'camera=()'}

def page(base, robots='', form=None):
    flag = f'<form data-enabled={form}></form>' if form else ''
    return f'<!doctype html><title>T</title><link rel=canonical href={base}/>{robots}<h1>Hi</h1>{flag}'

def serve(routes, fallback):
    """A server answering `routes` (path -> (status, headers, body)) and `fallback` for anything else."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, headers, body = routes.get(self.path, fallback)
            payload = body.replace('{base}', f'http://127.0.0.1:{self.server.server_address[1]}').encode()
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f'http://127.0.0.1:{server.server_address[1]}'

def healthy(indexable=True, form='true'):
    robots = '' if indexable else '<meta name=robots content=noindex>'
    return {
        '/': (200, SECURE, page('{base}', robots)),
        '/contact/': (200, SECURE, page('{base}', robots, form)),
        '/__smoke-missing-page__/': (404, SECURE, '<meta name=robots content=noindex><h1>Not here</h1>'),
        '/.factory-build.json': (404, SECURE, ''),
        '/api/contact': (405, {}, '{}'),
        '/robots.txt': (200, {}, 'User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n'),
        '/sitemap.xml': (200, {}, '<urlset><url><loc>{base}/</loc></url></urlset>'),
    }

class SmokeTests(unittest.TestCase):
    def run_smoke(self, routes, fallback, *args):
        server, base = serve(routes, fallback)
        self.addCleanup(server.shutdown)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = smoke.main([base, *args])
        return code, out.getvalue()

    def test_a_healthy_production_release_passes(self):
        code, out = self.run_smoke(healthy(), (404, SECURE, ''), '--form', 'on')
        self.assertEqual(code, 0, out)
        self.assertNotIn('FAIL', out)

    def test_a_healthy_preview_passes_only_as_a_preview(self):
        routes = healthy(indexable=False, form='false')
        code, out = self.run_smoke(routes, (404, SECURE, ''), '--noindex', '--form', 'off')
        self.assertEqual(code, 0, out)
        code, out = self.run_smoke(routes, (404, SECURE, ''), '--form', 'off')
        self.assertEqual(code, 1, 'a noindex page is wrong for production')
        self.assertIn('FAIL  search engines allowed in', out)

    def test_a_preview_may_keep_the_placeholder_domain_but_production_may_not(self):
        # preview.yml builds without the real base URL, so its canonical is example.invalid by design.
        routes = healthy(indexable=False, form='false')
        routes['/'] = (200, SECURE, page('https://example.invalid', '<meta name=robots content=noindex>'))
        code, out = self.run_smoke(routes, (404, SECURE, ''), '--noindex', '--form', 'off')
        self.assertEqual(code, 0, out)
        code, out = self.run_smoke(routes, (404, SECURE, ''), '--form', 'off')
        self.assertIn('FAIL  canonical is this site', out)
        self.assertIn('FAIL  no placeholder domain', out)

    def test_the_stale_build_that_fell_back_to_the_home_page_is_caught(self):
        # What 258webco.com served on 2026-09-29: an old build, every address answers 200, no security
        # headers, no endpoint, the placeholder domain, and a contact form switched off.
        home = (200, {}, page('https://example.invalid', '', 'false') + '<p>To be confirmed</p>')
        code, out = self.run_smoke({'/robots.txt': (200, {}, 'User-agent: *\nDisallow: /\n')}, home, '--form', 'on')
        self.assertEqual(code, 1)
        for expected in ('canonical is this site', 'no placeholder domain', 'security headers present',
                         'an unknown address answers 404', 'the build inventory is not public',
                         'the contact endpoint is the current one', 'contact form is switched on', 'robots.txt allows crawling'):
            self.assertIn(f'FAIL  {expected}', out)

    def test_no_endpoint_skips_only_that_check(self):
        routes = healthy()
        routes['/api/contact'] = (404, {}, '')
        code, _ = self.run_smoke(routes, (404, SECURE, ''), '--form', 'on')
        self.assertEqual(code, 1)
        code, out = self.run_smoke(routes, (404, SECURE, ''), '--form', 'on', '--no-endpoint')
        self.assertEqual(code, 0, out)

def routed(path, rule):
    """Cloudflare's documented _routes.json matching: * matches anything, across slashes; "/x/*" also matches "/x"."""
    if rule.endswith('/*') and path == rule[:-2]:
        return True
    return re.fullmatch('.*'.join(re.escape(part) for part in rule.split('*')), path) is not None

class RoutesTests(unittest.TestCase):
    """static/_routes.json runs Functions only for the endpoint and the dotfiles the middleware hides.
    Cloudflare applies it on deploy; the preview workflow's smoke check proves the dotfile rule there."""
    routes = json.loads((Path(__file__).resolve().parents[1] / 'static/_routes.json').read_text())

    def runs_function(self, path):
        return (any(routed(path, rule) for rule in self.routes['include'])
                and not any(routed(path, rule) for rule in self.routes['exclude']))

    def test_limits(self):
        rules = self.routes['include'] + self.routes['exclude']
        self.assertEqual(self.routes['version'], 1)
        self.assertTrue(self.routes['include'], 'at least one include rule')
        self.assertLessEqual(len(rules), 100)
        self.assertTrue(all(len(rule) <= 100 for rule in rules))

    def test_endpoint_and_private_files_reach_the_function(self):
        for path in ('/api/contact', '/.factory-build.json', '/.factory-receipt.json', '/.env', '/.git/config'):
            self.assertTrue(self.runs_function(path), path)

    def test_every_function_file_is_routed(self):
        functions = Path(__file__).resolve().parents[1] / 'functions'
        for file in functions.rglob('*.js'):
            if file.name == '_middleware.js':
                continue
            path = '/' + re.sub(r'\[[^/]+\]', 'x', file.relative_to(functions).with_suffix('').as_posix())
            self.assertTrue(self.runs_function(path), f'{file.name} answers {path}; add it to static/_routes.json include')

    def test_pages_and_assets_skip_it(self):
        for path in ('/', '/contact/', '/contact/received/', '/css/main.css', '/fonts/inter-latin-variable.woff2',
                     '/factory-release.json', '/.well-known/security.txt', '/apiary/', '/a/.hidden'):
            self.assertFalse(self.runs_function(path), path)

class WorkflowTests(unittest.TestCase):
    def test_actions_are_pinned_to_commits(self):
        """The deploy workflows hold the Cloudflare token, so each action is an exact commit, not a movable tag."""
        for workflow in (Path(__file__).resolve().parents[1] / '.github/workflows').glob('*.yml'):
            for line in workflow.read_text().splitlines():
                if line.strip().startswith(('uses:', '- uses:')):
                    self.assertRegex(line, r'uses: [\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d', f'{workflow.name}: {line.strip()}')

if __name__ == '__main__':
    unittest.main()
