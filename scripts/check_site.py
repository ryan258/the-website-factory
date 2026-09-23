#!/usr/bin/env python3
"""Check generated HTML, metadata, local references, and compressed asset budgets."""
import argparse
import gzip
import os
import re
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from factory import contact_link_error  # noqa: E402

def noindex_expected():
    """Search-engine visibility is a deliberate release setting, not a template edit."""
    found = re.search(r'(?m)^\s*noindex\s*=\s*(\w+)', (ROOT/'hugo.toml').read_text())
    return os.environ.get('HUGO_PARAMS_NOINDEX', found.group(1) if found else 'true').lower() not in ('false', '0', 'no')
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.h1=0; self.title=''; self.in_title=False; self.meta={}; self.canonical=''; self.refs=[]; self.ids=[]; self.loads=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='h1': self.h1+=1
        if tag=='title': self.in_title=True
        if 'id' in a: self.ids.append(a['id'])
        if tag=='meta': self.meta[a.get('name','')]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical': self.canonical=a.get('href','')
        if tag=='a' and a.get('href'): self.refs.append(a['href'])
        if tag in ('img','script') and a.get('src'): self.refs.append(a['src']); self.loads.append(a['src'])
        if tag=='link' and a.get('rel') in ('stylesheet','preload','icon','apple-touch-icon'): self.refs.append(a.get('href','')); self.loads.append(a.get('href',''))
        if tag in ('img','source') and a.get('srcset'): self.loads+=[c.split()[0] for c in a['srcset'].split(',') if c.strip()]
    def handle_endtag(self, tag):
        if tag=='title': self.in_title=False
    def handle_data(self, value):
        if self.in_title:self.title+=value

def check(output, noindex=None):
    noindex = noindex_expected() if noindex is None else noindex
    errors=[]; pages={}
    for file in output.rglob('*.html'):
        p=Page();p.feed(file.read_text());pages[file.resolve()]=p
    if not pages:return ['No generated HTML found. Run scripts/build.py first.']
    for field in ('title','canonical'):
        values=[getattr(p,field) for p in pages.values()]
        if len(set(values))!=len(values) or not all(values): errors.append(f'{field}: empty or duplicate values')
    descriptions=[p.meta.get('description','') for p in pages.values()]
    if not all(descriptions) or len(set(descriptions))!=len(descriptions):errors.append('Descriptions: empty or duplicate values')
    # An indexable build is a public release; it must name its real domain, not the placeholder.
    placeholder=[p.canonical for p in pages.values() if (urlparse(p.canonical).hostname or '').endswith('example.invalid')]
    if not noindex and placeholder:errors.append(f'Indexable build still uses the placeholder domain: {placeholder[0]}. Build with --base-url set to the real domain.')
    for file,p in pages.items():
        label=str(file.relative_to(output))
        # Unconfirmed facts are marked "To be confirmed" (scripts/from_plan.py, draft_plan.py); a public release must not show one.
        if not noindex:
            found=re.search(r'(?i)to be confirmed|lorem ipsum',file.read_text())
            if found:errors.append(f'{label}: placeholder text "{found.group(0)}" in an indexable build; replace it with a confirmed fact')
        if p.h1!=1:errors.append(f'{label}: expected one H1')
        if len(p.title)>=60:errors.append(f'{label}: title must be under 60 characters')
        if len(p.meta.get('description',''))>=155:errors.append(f'{label}: description must be under 155 characters')
        if noindex and p.meta.get('robots')!='noindex':errors.append(f'{label}: noindex missing')
        if not noindex and p.meta.get('robots')=='noindex':errors.append(f'{label}: noindex present in an indexable build')
        if len(set(p.ids))!=len(p.ids):errors.append(f'{label}: duplicate IDs')
        base=urlparse(p.canonical)
        # The CSP in static/_headers allows only this site's own files; catch any other origin here.
        for ref in p.loads:
            u=urlparse(ref)
            if (u.scheme or u.netloc) and u.netloc!=base.netloc:errors.append(f'{label}: loads a file from another site: {ref}')
        rel=file.relative_to(output).as_posix()
        suffix='/' if rel=='index.html' else '/'+rel.removesuffix('index.html')
        prefix=base.path[:-len(suffix)] if base.path.endswith(suffix) else ''
        for ref in p.refs:
            # Hugo swaps a URL it considers unsafe for this marker instead of failing the build.
            if 'ZgotmplZ' in ref:errors.append(f'{label}: a link was replaced as unsafe ({ref}); mark it with safeURL only after validating it');continue
            if ref.startswith(('mailto:','tel:')):
                problem=contact_link_error(unquote(ref))
                if problem:errors.append(f'{label}: {problem}')
                continue
            u=urlparse(ref)
            if u.scheme or u.netloc:continue
            path=unquote(u.path)
            if path.startswith('/'):
                if prefix and not path.startswith(prefix+'/'):
                    errors.append(f'{label}: reference escapes base path: {ref}')
                    continue
                if prefix:path=path[len(prefix):]
                target=(output/path.lstrip('/')).resolve()
            elif path:target=(file.parent/path).resolve()
            else:target=file
            if target.is_dir():target=target/'index.html'
            if not target.exists():errors.append(f'{label}: missing {ref}')
            elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:errors.append(f'{label}: missing anchor {ref}')
    for directory,extension,budget in [('css','css',20000),('js','js',5000)]:
        # The internal editor has a separate budget; public-site bundles retain their limits.
        for asset in (output/directory).glob('*.'+extension):
            limit = 9000 if directory == 'js' and asset.name.startswith('workflow.') and (output/'site-kit/index.html').exists() else budget
            if len(gzip.compress(asset.read_bytes())) >= limit:
                errors.append(f'{directory}/{asset.name}: compressed bundle exceeds {limit} bytes')
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',nargs='?',default=str(ROOT/'public'))
    parser.add_argument('--json',action='store_true',help='Print a machine-readable result with an error code per problem');args=parser.parse_args()
    errors=check(Path(args.output).resolve())
    if args.json:
        from report import emit
        return emit(errors,output=args.output,noindex=noindex_expected())
    if errors:print('\n'.join(errors),file=sys.stderr);return 1
    print(f'Static checks passed: unique metadata, H1, robots ({"noindex" if noindex_expected() else "indexable"}), references, anchors, and compressed CSS/JS budgets.');return 0
if __name__=='__main__':sys.exit(main())
