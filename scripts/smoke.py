#!/usr/bin/env python3
"""Read-only checks of a deployed site: is what is live the release you meant to ship?

  python3 scripts/smoke.py https://258webco.com --form on
  python3 scripts/smoke.py https://preview-site.258webco.pages.dev --noindex --form off

Sends GET requests only. It never submits the contact form. Exit 1 if any check fails.
--noindex expects a preview (search engines kept out); --form says whether the contact form should
be switched on; --no-endpoint skips the /api/contact check for a site that uses an outside form service.
"""
import argparse
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

HEADERS = ('content-security-policy', 'strict-transport-security', 'x-content-type-options', 'x-frame-options',
           'referrer-policy', 'permissions-policy')

def fetch(url):
    """(status, lower-cased headers, text) for a GET; an HTTP error status is an answer, not a failure."""
    request = urllib.request.Request(url, headers={'User-Agent': 'factory-smoke/1'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read().decode('utf-8', 'replace')

def robots_meta(html):
    found = re.search(r'<meta[^>]+name=["\']?robots["\']?[^>]*content=["\']?([^"\'>]*)', html)
    return found.group(1) if found else ''

def check_site(base, noindex=False, form='any', endpoint=True):
    """A list of (ok, what, detail). Every request is a GET."""
    results = []
    def check(ok, what, detail=''):
        results.append((bool(ok), what, detail))
    host = urlsplit(base).hostname
    check(base.startswith('https://') or host in ('127.0.0.1', 'localhost'), 'served over https', base)
    status, headers, home = fetch(base + '/')
    check(status == 200, 'home page answers 200', str(status))
    canonical = re.search(r'rel=["\']?canonical["\']?[^>]*href=["\']?([^\s"\'>]+)', home)
    check(canonical and canonical.group(1) == base + '/', 'canonical is this site\'s real address',
          canonical.group(1) if canonical else 'no canonical link')
    check('example.invalid' not in home and 'to be confirmed' not in home.lower(), 'no placeholder domain or "To be confirmed"')
    robots = robots_meta(home) + ' ' + headers.get('x-robots-tag', '')
    check(('noindex' in robots) == noindex, 'search engines ' + ('kept out (preview)' if noindex else 'allowed in'), robots.strip() or 'no robots directive')
    missing = [name for name in HEADERS if name not in headers]
    check(not missing, 'security headers present', 'missing: ' + ', '.join(missing))
    csp = headers.get('content-security-policy', '')
    check("default-src 'self'" in csp and "frame-ancestors 'none'" in csp, 'CSP allows only this site', csp[:60] or 'no CSP')
    status, _, page = fetch(base + '/__smoke-missing-page__/')
    check(status == 404, 'an unknown address answers 404, not the home page', str(status))
    check(status == 404 and 'noindex' in robots_meta(page), 'the 404 page is noindex', 'no 404 page' if status != 404 else 'indexable')
    status, _, _ = fetch(base + '/.factory-build.json')
    check(status == 404, 'the build inventory is not public', str(status))
    if endpoint:
        status, _, _ = fetch(base + '/api/contact')
        check(status == 405, 'the contact endpoint is the current one (GET answers 405)', str(status))
    if form != 'any':
        status, _, contact = fetch(base + '/contact/')
        flag = re.search(r'data-enabled=["\']?(true|false)', contact)
        check(status == 200 and flag and flag.group(1) == ('true' if form == 'on' else 'false'),
              f'contact form is switched {form}', flag.group(1) if flag else f'no form flag (HTTP {status})')
    if not noindex:
        status, _, robots_txt = fetch(base + '/robots.txt')
        check(status == 200 and 'sitemap:' in robots_txt.lower() and not re.search(r'(?im)^disallow:\s*/\s*$', robots_txt),
              'robots.txt allows crawling and names the sitemap', str(status))
        status, _, sitemap = fetch(base + '/sitemap.xml')
        urls = re.findall(r'<loc>([^<]+)</loc>', sitemap)
        check(status == 200 and urls and all(u.startswith(base + '/') for u in urls), 'sitemap lists this site\'s pages', f'{len(urls)} address(es)')
    return results

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('url', help='Site address, e.g. https://258webco.com')
    parser.add_argument('--noindex', action='store_true', help='Expect a preview that keeps search engines out')
    parser.add_argument('--form', choices=('on', 'off', 'any'), default='any', help='Expected state of the contact form')
    parser.add_argument('--no-endpoint', action='store_true', help='Skip the /api/contact check')
    args = parser.parse_args(argv)
    results = check_site(args.url.rstrip('/'), noindex=args.noindex, form=args.form, endpoint=not args.no_endpoint)
    for ok, what, detail in results:
        print(f'{"ok  " if ok else "FAIL"}  {what}' + ('' if ok or not detail else f' -- {detail}'))
    failed = sum(not ok for ok, _, _ in results)
    print(f'{len(results) - failed}/{len(results)} checks passed.' if not failed else f'{failed} check(s) failed: this is not the release you meant to ship.')
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
