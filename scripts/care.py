#!/usr/bin/env python3
"""Care-plan check for live client sites: smoke.py's checks, plus certificate expiry, the
http-to-https redirect, and response time, written up as a report you can send.

  ./wf care https://client.example --form on      # one site, with smoke.py's options
  ./wf care                                       # every site in care-sites.txt
  ./wf care --sites other-list.txt

care-sites.txt has one site per line, written like smoke.py's arguments; # starts a note:

  https://258webco.com --form on
  https://client.example --no-endpoint            # uses an outside form service

The file stays out of Git and is kept by ./wf backup. Every request is a GET; the contact
form is never submitted. Reports are saved under reports/care/. Exit 1 when any check FAILs.
"""
import argparse
from datetime import datetime, timezone
import http.client
from pathlib import Path
import shlex
import socket
import ssl
import sys
import time
from urllib.parse import urlsplit

import smoke

ROOT = Path(__file__).resolve().parents[1]
SLOW_MS = 2000
CERT_WARN_DAYS = 14

def cert_days_left(host, port=443):
    with socket.create_connection((host, port), timeout=15) as raw:
        with ssl.create_default_context().wrap_socket(raw, server_hostname=host) as tls:
            not_after = tls.getpeercert()['notAfter']
    return int((ssl.cert_time_to_seconds(not_after) - time.time()) // 86400)

def plain_http(host):
    """(status, Location) for http://host/, without following the redirect."""
    connection = http.client.HTTPConnection(host, timeout=15)
    try:
        connection.request('GET', '/', headers={'User-Agent': 'factory-care/1'})
        response = connection.getresponse()
        return response.status, response.getheader('Location', '')
    finally:
        connection.close()

def care_checks(base, cert=cert_days_left, redirect=plain_http):
    """The checks smoke.py does not make, as (status, what, detail); status is ok, WARN or FAIL."""
    results = []
    started = time.monotonic()
    smoke.fetch(base + '/')
    ms = (time.monotonic() - started) * 1000
    results.append(('ok' if ms <= SLOW_MS else 'WARN', f'home page loads in {ms:.0f} ms',
                    '' if ms <= SLOW_MS else f'over the {SLOW_MS} ms budget; check again before acting'))
    parts = urlsplit(base)
    if parts.scheme != 'https':
        return results
    try:
        days = cert(parts.hostname, parts.port or 443)
        results.append(('ok' if days > CERT_WARN_DAYS else 'WARN', f'certificate valid for {days} more days',
                        '' if days > CERT_WARN_DAYS else 'renewal is due; check the host renews it'))
    except (OSError, KeyError, ValueError) as error:
        results.append(('FAIL', 'certificate could not be checked', str(error)))
    try:
        status, location = redirect(parts.netloc)
        moved = status in (301, 302, 307, 308) and location.startswith('https://')
        results.append(('ok' if moved else 'WARN', 'http:// sends visitors to https://', '' if moved else f'answered {status}'))
    except OSError:
        results.append(('ok', 'http:// does not answer, so no visitor lands on an insecure page', ''))
    return results

def check_line(line, **options):
    """All checks for one care-sites.txt line."""
    try:
        args = smoke.parser().parse_args(shlex.split(line))
    except (SystemExit, ValueError):
        return [('FAIL', f'cannot read this line: {line}', 'use smoke.py options, e.g. https://site.example --form on')]
    try:
        results = [('ok' if ok else 'FAIL', what, detail) for ok, what, detail in smoke.run(args)]
        return results + care_checks(args.url.rstrip('/'), **options)
    except (OSError, ValueError, KeyError) as error:
        return [('FAIL', 'site did not answer', str(getattr(error, 'reason', error)))]

def report(lines, now=None, **options):
    now = now or datetime.now().astimezone()  # the reader's own date, not UTC's
    text, failed = [f'# Site care check, {now:%d %B %Y}', '',
                    'Each check only reads the live site. WARN needs a look; FAIL needs action.', ''], False
    for line in lines:
        results = check_line(line, **options)
        failed |= any(status == 'FAIL' for status, _, _ in results)
        text += [f'## {line.split()[0]}', '']
        text += [f'- **{status}** {what}' + (f': {detail}' if detail and status != 'ok' else '') for status, what, detail in results]
        text.append('')
    return '\n'.join(text), failed

def read_sites(path):
    return [line.split(' #')[0].strip() for line in Path(path).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#')]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sites', help='Site list, one smoke.py command line per site (default: care-sites.txt)')
    parser.add_argument('--no-save', action='store_true', help='Print the report without saving it under reports/care/')
    args, site = parser.parse_known_args(argv)
    if site and not args.sites:
        lines = [shlex.join(site)]
    else:
        listing = Path(args.sites) if args.sites else ROOT / 'care-sites.txt'
        if not listing.is_file():
            parser.error(f'{listing} does not exist. Name a site, or list one per line in care-sites.txt.')
        lines = read_sites(listing)
        if not lines:
            parser.error(f'{listing} lists no sites.')
    text, failed = report(lines)
    print(text)
    if not args.no_save:
        target = ROOT / 'reports/care' / f'{datetime.now(timezone.utc):%Y-%m-%dT%H%M%SZ}.md'  # UTC sorts and never repeats
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        print(f'Saved {target.relative_to(ROOT)}', file=sys.stderr)
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
