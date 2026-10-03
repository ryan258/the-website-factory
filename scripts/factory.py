#!/usr/bin/env python3
"""Validate and scaffold the declarative website factory using only the standard library."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from report import Issue

ROOT = Path(__file__).resolve().parents[1]
# mailto: and tel: links must hold something a visitor can actually use.
EMAIL = re.compile(r'[^@\s/?#:]+@[^@\s/?#:]+\.[a-zA-Z]{2,}')
TEL = re.compile(r'\+?[(0-9][0-9 ().-]{5,}')
ANCHOR = re.compile(r'[a-z][a-z0-9-]*')

def contact_link_error(url):
    """None if url is a usable mailto: or tel: link, else the reason it is not."""
    if url.startswith('mailto:'):
        return None if EMAIL.fullmatch(url[7:]) else f'mailto link needs one valid email address: {url}'
    digits = re.sub(r'\D', '', url[4:])
    return None if TEL.fullmatch(url[4:]) and 7 <= len(digits) <= 15 else f'tel link needs a phone number of 7-15 digits: {url}'

def read(path):
    return json.loads(path.read_text())

def yaml_scalar(raw):
    """One-line YAML scalar: "double" (JSON escapes), 'single' ('' is a quote), or plain with an optional # comment."""
    raw = raw.strip()
    if raw.startswith('"'):
        return json.loads(raw[:raw.rindex('"')+1])
    if raw.startswith("'"):
        return raw[1:raw.rindex("'")].replace("''", "'")
    return re.sub(r'\s+#.*$', '', raw)

def validate(root=ROOT, workshop=None, extra_presets=None):
    errors = []
    def fail(message, code, path=None, hint=None):
        """Record an error with its code, a JSON pointer into the preset, and what to do about it."""
        errors.append(Issue(message, code, path, hint))
    try:
        config = read(root / 'data/factory.json')
        if not isinstance(config, dict):
            return [Issue('data/factory.json: expected object', 'CONFIG_SHAPE_INVALID', '', 'use an object with preset and workshop')]
        if workshop is not None:
            config['workshop'] = workshop
        registry = read(root / 'data/modules.json')
        profiles = {p.stem: read(p) for p in (root / 'data/presets').glob('*.json')}
        if extra_presets:
            profiles.update(extra_presets)
        examples = read(root / 'data/examples.json') if config.get('workshop') else {}
        tones = read(root / 'data/tones.json')
        palettes = read(root / 'data/palettes.json')
        font_pairings = read(root / 'data/fonts.json')
    except (OSError, ValueError) as error:
        return [str(error)]
    # Shape errors must stop before semantic rules index nested objects or hash keys.
    from schemas import preset_schema, validate as validate_shape
    shape = preset_schema(registry, tones, palettes, font_pairings)
    for slug, profile in profiles.items():
        for problem in validate_shape(profile, shape):
            if ': expected ' in problem:
                fail(f'{slug}: {problem}', 'PRESET_SHAPE_INVALID', '', 'repair the named field before semantic validation')
    if errors:
        return errors
    if config.get('preset') not in profiles:
        fail('data/factory.json: unknown selected preset', 'PRESET_UNKNOWN', '/preset', 'set "preset" to a file name in data/presets/')
    if type(config.get('workshop')) is not bool:
        fail('data/factory.json: workshop must be true or false', 'CONFIG_WORKSHOP_INVALID', '/workshop', 'use true or false')
    # The header, footer, titles, and structured data read data/site.yaml, while the pages read
    # the preset. A mismatch published one business's pages under another's name, so it fails.
    named=re.search(r'(?m)^name:\s*(.+?)\s*$', (root/'data/site.yaml').read_text()) if (root/'data/site.yaml').is_file() else None
    site_name=yaml_scalar(named.group(1)) if named else None
    errors+=font_errors(root)
    if config.get('preset') in profiles and site_name!=profiles[config['preset']].get('name'):
        preset_name = profiles[config['preset']].get('name')
        fail(f"data/site.yaml: name {site_name!r} must match the selected preset's name {preset_name!r}", 'SITE_NAME_MISMATCH',
             None, f'set "name" in data/site.yaml to {preset_name!r}, or rename the preset')
    def check_content(module, content, label, profile=None, at=None):
        def loc(*parts):
            return None if at is None else at + ''.join(f'/{part}' for part in parts)
        if not isinstance(content, dict):
            fail(f'{label}: content must be an object', 'CONTENT_TYPE_INVALID', loc(), 'this section needs a content object'); return
        types = [e for e in validate_shape(content, shape['$defs'][f'content-{module}'], shape) if ': expected ' in e]
        if types:
            for problem in types:
                fail(f'{label}: {problem}', 'CONTENT_TYPE_INVALID', loc(), 'repair the named content type')
            return
        for field in registry[module]['required']:
            if not content.get(field): fail(f'{label}: missing required field {field}', 'CONTENT_FIELD_MISSING', loc(field), f'add "{field}" to this content')
        for field in ('title','intro','body','notice','label','aside','note','image','imageAlt'):
            if field in content and not isinstance(content[field], str): fail(f'{label}: {field} must be text', 'CONTENT_TYPE_INVALID', loc(field), 'use a text value')
        if content.get('image') and isinstance(content['image'], str):
            image = Path(content['image'])
            if image.is_absolute() or '..' in image.parts or not (root/'assets'/image).is_file():
                fail(f'{label}: missing or unsafe image {image}', 'CONTENT_IMAGE_INVALID', loc('image'), 'use a file under assets/, such as images/name.webp')
            if not isinstance(content.get('imageAlt'), str) or not content['imageAlt'].strip():
                fail(f'{label}: image needs descriptive imageAlt text', 'CONTENT_IMAGE_ALT_MISSING', loc('imageAlt'), 'describe what the image shows')
        if module == 'project-brief':
            options = content.get('services')
            if not isinstance(options, list) or not options or not all(isinstance(option, str) and option.strip() for option in options):
                fail(f'{label}: services must be a nonempty list of service names', 'CONTENT_TYPE_INVALID', loc('services'), 'list the services a visitor can pick')
            elif len(set(options)) != len(options):
                fail(f'{label}: services must not contain duplicates', 'CONTENT_ITEM_INVALID', loc('services'), 'remove the repeated service names')
            elif profile:
                offered = set()
                for page in profile.get('pages', {}).values():
                    for section in page.get('sections', []) if isinstance(page, dict) else []:
                        if section.get('module') == 'services':
                            data = profile.get('sections', {}).get(section.get('content'), {})
                            offered.update(item.get('title') for item in data.get('items', []) if isinstance(item, dict))
                missing = set(options) - offered
                if missing:
                    fail(f'{label}: project brief includes services absent from the site catalog: {", ".join(sorted(missing))}', 'CONTENT_SERVICE_UNKNOWN',
                         loc('services'), 'use titles from the services module, or add those services there')
        if 'items' in registry[module]['required']:
            if not isinstance(content.get('items'), list) or not content['items']:
                fail(f'{label}: items must be a nonempty list', 'CONTENT_ITEM_INVALID', loc('items'), 'add at least one item with a title and text'); return
            for i, item in enumerate(content['items']):
                if not isinstance(item, dict) or not all(isinstance(item.get(k),str) and item[k].strip() for k in ('title','text')):
                    fail(f'{label}: item {i+1} needs title and text', 'CONTENT_ITEM_INVALID', loc('items', i), 'give this item a title and text'); continue
                for field in registry[module].get('item_required', []):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        fail(f'{label}: item {i+1} needs {field}', 'CONTENT_ITEM_INVALID', loc('items', i, field), f'add "{field}" to this item')
                for field, choices in registry[module].get('item_choices', {}).items():
                    if item.get(field) not in choices:
                        fail(f'{label}: item {i+1} has unsupported {field}', 'CONTENT_ITEM_CHOICE_INVALID', loc('items', i, field), f'choose one of: {", ".join(map(str, choices))}')
                if module == 'comparison' and not all(item.get(k) for k in ('scope','best')):
                    fail(f'{label}: comparison needs scope and best', 'CONTENT_ITEM_INVALID', loc('items', i), 'add "scope" and "best" to this item')
                if item.get('image'):
                    image = Path(item['image'])
                    if image.is_absolute() or '..' in image.parts or not (root/'assets'/image).is_file():
                        fail(f'{label}: missing or unsafe image {image}', 'CONTENT_IMAGE_INVALID', loc('items', i, 'image'), 'use a file under assets/, such as images/name.webp')
                    if 'imageAlt' in item and not isinstance(item['imageAlt'], str):
                        fail(f'{label}: item {i+1} imageAlt must be text', 'CONTENT_TYPE_INVALID', loc('items', i, 'imageAlt'), 'use a text value')
        for field in ('action','secondary'):
            if field in content and (not isinstance(content[field],dict) or not content[field].get('label') or not content[field].get('url')):
                fail(f'{label}: {field} needs label and url', 'CONTENT_ACTION_INVALID', loc(field), 'give the button a "label" and a "url"')
        def links(value, where):
            if isinstance(value,dict):
                for key, val in value.items():
                    if key=='url':
                        here=loc(*where, key)
                        if not isinstance(val,str): fail(f'{label}: URL must be text', 'CONTENT_ACTION_INVALID', here, 'use a text address'); continue
                        if val.startswith(('mailto:','tel:')):
                            problem=contact_link_error(val)
                            if problem: fail(f'{label}: {problem}', 'CONTENT_CONTACT_LINK_INVALID', here, 'use one valid email address, or a phone number of 7-15 digits')
                            continue
                        parsed=urlsplit(val)
                        if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password and not any(c.isspace() for c in val):
                            continue
                        if parsed.scheme or parsed.netloc or not val.startswith('/') or '..' in parsed.path.split('/') or parsed.query or (parsed.fragment and not ANCHOR.fullmatch(parsed.fragment)):
                            fail(f'{label}: module links must be local page paths, https:, mailto:, or tel: {val}', 'CONTENT_LINK_INVALID', here, 'use a local path or a credential-free HTTPS, mailto: or tel: address'); continue
                        parts=parsed.path.strip('/').split('/')
                        page=parts[0] or 'home'
                        if profile and page not in profile['pages']:
                            fail(f'{label}: link to omitted page {val}', 'CONTENT_LINK_INVALID', here, f'add a "{page}" page, or point the link at a page that exists')
                        elif profile and parsed.fragment and isinstance(profile['pages'][page],dict):
                            # A deep link must land on a section that declares that anchor.
                            declared={s.get('anchor') for s in profile['pages'][page].get('sections',[]) if isinstance(s,dict)}
                            if parsed.fragment not in declared:
                                fail(f'{label}: link to missing anchor {val}; add "anchor": "{parsed.fragment}" to a section on that page', 'CONTENT_ANCHOR_INVALID',
                                     here, f'add "anchor": "{parsed.fragment}" to a section on the {page} page')
                        path=root/'content'/parsed.path.strip('/')
                        if page!='home' and not any(p.is_file() for p in [path/'_index.md',path/'index.md',path.with_suffix('.md')]):
                            fail(f'{label}: link has no content page: {val}', 'CONTENT_LINK_INVALID', here, f'add content/{parsed.path.strip("/")}/_index.md, or change the link')
                    else: links(val, where+(key,))
            elif isinstance(value,list):
                for n, item in enumerate(value): links(item, where+(n,))
        links(content, ())
    for slug, profile in profiles.items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug): fail(f'Invalid preset identifier {slug}', 'PRESET_KEY_INVALID', None, 'use lowercase letters, digits, and hyphens')
        for field, choices in [('site_type', ('business', 'creator')), ('contact_mode', ('inquiry', 'email', 'link', 'off'))]:
            if field in profile and profile[field] not in choices:
                fail(f'{slug}: unsupported {field}', 'PRESET_MODE_INVALID', f'/{field}', 'choose one of: ' + ', '.join(choices))
        approved=profile.get('approved_claims',[])
        if not isinstance(approved,list) or not all(isinstance(a,str) and a.strip() for a in approved):
            fail(f'{slug}: approved_claims must be a list of text', 'PRESET_CLAIMS_INVALID', '/approved_claims', 'use a list of the exact texts the business confirmed')
        if profile.get('tone') not in tones: fail(f"{slug}: unknown tone; choose one of {', '.join(tones)}", 'PRESET_TONE_UNKNOWN', '/tone', f'choose one of: {", ".join(tones)}')
        if profile.get('palette') and profile['palette'] not in palettes:
            fail(f"{slug}: unknown palette; choose one of {', '.join(palettes)}", 'PRESET_PALETTE_UNKNOWN', '/palette', f'choose one of: {", ".join(palettes)}')
        if profile.get('font_pairing') and profile['font_pairing'] not in font_pairings:
            fail(f"{slug}: unknown font pairing; choose one of {', '.join(font_pairings)}", 'PRESET_FONT_PAIRING_UNKNOWN', '/font_pairing', f'choose one of: {", ".join(font_pairings)}')
        if not isinstance(profile.get('pages'),dict) or not isinstance(profile.get('sections'),dict):
            fail(f'{slug}: pages and sections must be objects', 'PRESET_SHAPE_INVALID', '', 'a preset needs a "pages" object and a "sections" object'); continue
        creator = profile.get('site_type', 'business') == 'creator'
        contact_mode = profile.get('contact_mode', 'off' if creator else 'inquiry')
        required_pages = ('home', 'contact') if contact_mode == 'inquiry' else ('home',)
        if not all(k in profile['pages'] for k in required_pages):
            fail(f'{slug}: required pages: {", ".join(required_pages)}', 'PRESET_REQUIRED_PAGE_MISSING', '/pages', 'add the missing required pages')
        # The contact form offers the services module's own items as project types, whatever
        # content key it references. Without one there is nothing to offer, so fail here.
        if contact_mode == 'inquiry' and not any(s.get('module')=='services'
                for page in profile['pages'].values() if isinstance(page,dict)
                for s in (page.get('sections') or []) if isinstance(s,dict)):
            fail(f'{slug}: a services module is required somewhere; the contact form offers its items as project types', 'PRESET_SERVICES_MISSING', '/pages', 'add a "services" section to one page')
        for key,page in profile['pages'].items():
            if not re.fullmatch(r'[a-z][a-z0-9-]*',key): fail(f'{slug}: invalid page key {key}', 'PRESET_KEY_INVALID', f'/pages/{key}', 'use lowercase words joined by hyphens')
            if not isinstance(page,dict):
                fail(f'{slug}/{key}: page must be an object', 'CONTENT_TYPE_INVALID', f'/pages/{key}', 'a page needs a title, a description, and sections'); continue
            sections=page.get('sections')
            if not isinstance(sections,list) or not sections or not all(isinstance(s,dict) for s in sections):
                fail(f'{slug}/{key}: sections must be a nonempty list of objects', 'CONTENT_TYPE_INVALID', f'/pages/{key}/sections', 'give the page at least one section'); continue
            if not all(page.get(k) for k in ('title','description')): fail(f'{slug}/{key}: title and description required', 'PAGE_METADATA_MISSING', f'/pages/{key}', 'add a "title" and a "description"')
            if sections[0].get('module')!='hero' or sum(s.get('module')=='hero' for s in sections)!=1:
                fail(f'{slug}/{key}: exactly one hero must be first', 'PRESET_HERO_POSITION', f'/pages/{key}/sections', 'make the first section a hero and use no other hero on the page')
            anchors=[s['anchor'] for s in sections if 'anchor' in s]
            for anchor in anchors:
                if not isinstance(anchor,str) or not ANCHOR.fullmatch(anchor) or re.fullmatch(r'.*-\d+',anchor):
                    fail(f'{slug}/{key}: anchor {anchor!r} must be lowercase words joined by hyphens, not ending in a number', 'CONTENT_ANCHOR_INVALID', f'/pages/{key}/sections', 'use lowercase words joined by hyphens')
            if len(set(map(str,anchors)))!=len(anchors):
                fail(f'{slug}/{key}: two sections share an anchor', 'CONTENT_ANCHOR_INVALID', f'/pages/{key}/sections', 'give each section its own anchor')
            for n,section in enumerate(sections):
                module=section.get('module');label=f'{slug}/{key}/{module}';at=f'/pages/{key}/sections/{n}'
                if module not in registry:
                    fail(f'{label}: unknown module', 'MODULE_UNKNOWN', f'{at}/module', f'choose one of: {", ".join(registry)}'); continue
                if section.get('variant') not in registry[module]['variants']: fail(f'{label}: unknown variant', 'MODULE_VARIANT_UNKNOWN', f'{at}/variant', f'choose one of: {", ".join(registry[module]["variants"])}')
                for dependency in registry[module].get('dependencies',[]):
                    if dependency not in profile['pages']: fail(f'{label}: requires page {dependency}', 'MODULE_DEPENDENCY_MISSING', f'{at}/module', f'add a "{dependency}" page, or remove this section')
                content_key=section.get('content')
                if not isinstance(profile['sections'].get(content_key),dict):
                    fail(f'{label}: content must be an object', 'CONTENT_TYPE_INVALID', f'{at}/content',
                         f'add "{content_key}" to "sections", or point "content" at an entry that exists' if content_key
                         else 'set "content" to the name of an entry in "sections"'); continue
                check_content(module,profile['sections'][content_key],label,profile,at=f'/sections/{content_key}')
    for module,content in examples.items():
        if module not in registry: fail(f'Unknown catalog module {module}', 'MODULE_UNKNOWN', None, f'choose one of: {", ".join(registry)}')
        else: check_content(module,content,f'catalog/{module}')
    return errors

def replace_block(text, key, value):
    """Set a top-level site.yaml key to one-line JSON, whether it is currently a block or already
    one line (a copy can be re-sculpted with another preset, which runs this twice)."""
    return re.sub(r'^'+key+r':(?:[ \t]*\n(?:[ \t]+.*\n)*|[ \t]+\S.*\n)', lambda _: key+': '+json.dumps(value)+'\n', text, flags=re.M)

def internal_links(value):
    """Every site-internal path anywhere in a JSON-ish structure, fragments and queries removed.

    Walking the whole structure instead of naming fields means action, secondary, item and any
    field added later all count as links, so a detail page is never dropped because the link
    that reaches it lives in a field this function had not heard of."""
    found = set()
    def walk(node):
        if isinstance(node, dict):
            for item in node.values(): walk(item)
        elif isinstance(node, (list, tuple)):
            for item in node: walk(item)
        elif isinstance(node, str):
            # The string itself (a JSON field), a Markdown link target, or a quoted path in YAML
            # front matter. Over-retaining is the safe direction: a path only counts once it
            # matches a page that actually exists.
            for raw in [node] + re.findall(r'\]\(([^)\s]+)\)', node) + re.findall(r'["\'](/[^"\'\s]*)["\']', node):
                if raw.startswith('/'):
                    found.add(re.split(r'[#?]', raw, maxsplit=1)[0])
    walk(value)
    return found

IMAGE_REF = re.compile(r'images/[\w./-]+\.(?:png|webp|jpe?g|svg|avif)')

def referenced_assets(profile, content_root):
    """Every images/... path the preset or any remaining content file refers to."""
    found = set(IMAGE_REF.findall(json.dumps(profile)))
    root = Path(content_root)
    if root.is_dir():
        for page in root.rglob('*.md'):
            found |= set(IMAGE_REF.findall(page.read_text()))
    return found

def retained_details(content_root, profile):
    """(kept, dropped) detail page files, by the rule the build itself applies.

    Links are followed transitively: a retained detail page's own front matter and Markdown can
    reach further detail pages, and those are kept too. scripts/claims.py reads this too, so what
    gets scanned for unconfirmed claims is exactly what gets rendered."""
    root = Path(content_root)
    linked = internal_links(profile)
    details = {}
    for section in ('services', 'work'):
        directory = root / section
        if not directory.is_dir():
            continue
        for page in directory.glob('*.md'):
            if page.name != '_index.md':
                details[f'/{section}/{page.stem}/'] = page
    # Fixed point: keeping a page can pull in whatever that page links to.
    keep, frontier = set(), linked & set(details)
    while frontier:
        keep |= frontier
        reached = set()
        for url in frontier:
            reached |= internal_links(details[url].read_text())
        frontier = (reached & set(details)) - keep
    return ([page for url, page in details.items() if url in keep],
            [page for url, page in details.items() if url not in keep])

def prune_unlinked_details(content_root, profile):
    """Remove detail pages nothing retained links to."""
    for page in retained_details(content_root, profile)[1]:
        page.unlink()

def apply_palette(destination, palette):
    """Replace the theme colors in a copy's data/site.yaml with a named palette from data/palettes.json."""
    root=Path(destination)
    palettes=read(root/'data/palettes.json')
    if palette not in palettes:
        raise ValueError(f"Unknown palette {palette!r}. Choose one of: {', '.join(palettes)}.")
    site=root/'data/site.yaml'
    text=site.read_text()
    block=re.search(r'(?m)^theme:\n((?:[ \t]+.*\n)+)',text)
    theme=block.group(1)
    for key,color in palettes[palette]['colors'].items():
        theme,count=re.subn(r'(?m)^([ \t]+'+key+r':).*$',lambda m:m.group(1)+' '+json.dumps(color),theme)
        if not count: raise ValueError(f'data/site.yaml theme has no {key} to replace.')
    site.write_text(text[:block.start(1)]+theme+text[block.end(1):])

FONT_KEYS=('family','file','weights','fallback','heading_family','heading_file','heading_weights','heading_fallback','tracking')

def font_settings(root):
    """The flat font block of data/site.yaml as a dict of strings."""
    block=re.search(r'(?m)^font:\n((?:[ \t]+.*\n)+)',(Path(root)/'data/site.yaml').read_text())
    return {k:yaml_scalar(v) for k,v in re.findall(r'(?m)^[ \t]+(\w+):[ \t]*(.*)$',block.group(1))} if block else {}

def font_errors(root):
    """Fonts must be self-hosted files with a license beside them; names and values must be plain."""
    font=font_settings(root); errors=[]
    for prefix in ('','heading_'):
        family,file=font.get(prefix+'family',''),font.get(prefix+'file','')
        if prefix and not (family or file): continue
        label=f'data/site.yaml font.{prefix}'
        if not re.fullmatch(r'[A-Za-z0-9 ]{1,60}',family): errors.append(f'{label}family must be a plain font name')
        path=Path(root)/'static'/file
        if not re.fullmatch(r'fonts/[a-z0-9-]+\.woff2',file) or not path.is_file():
            errors.append(f'{label}file must be an existing static/fonts/*.woff2 file'); continue
        stem=path.name.replace('-latin-variable.woff2','')
        if not ((path.parent/f'OFL-{stem}.txt').is_file() or (stem=='inter' and (path.parent/'OFL.txt').is_file())):
            errors.append(f'{label}file {file} has no license file (static/fonts/OFL-{stem}.txt)')
        weights=font.get(prefix+'weights') or font.get('weights','100 900')
        if not re.fullmatch(r'\d{3,4}( \d{3,4})?',weights): errors.append(f'{label}weights must look like "100 900"')
        if (font.get(prefix+'fallback') or 'sans-serif') not in ('serif','sans-serif'): errors.append(f'{label}fallback must be serif or sans-serif')
    if not re.fullmatch(r'-?\.?\d*\.?\d+em',font.get('tracking','-.045em')): errors.append('data/site.yaml font.tracking must be an em value such as -.02em')
    return errors

def apply_fonts(destination, pairing):
    """Set a copy's fonts from data/fonts.json and drop the font files (and licenses) it no longer uses."""
    root=Path(destination)
    pairings=read(root/'data/fonts.json')
    if pairing not in pairings:
        raise ValueError(f"Unknown font pairing {pairing!r}. Choose one of: {', '.join(pairings)}.")
    chosen=pairings[pairing]; body=chosen['body']; heading=chosen.get('heading') or {}
    values=dict(family=body['family'],file=body['file'],weights=body['weights'],fallback=body['fallback'],
                heading_family=heading.get('family',''),heading_file=heading.get('file',''),heading_weights=heading.get('weights',''),
                heading_fallback=heading.get('fallback',''),tracking=chosen['tracking'])
    site=root/'data/site.yaml'
    text=site.read_text()
    block=re.search(r'(?m)^font:\n((?:[ \t]+.*\n)+)',text)
    site.write_text(text[:block.start(1)]+''.join(f'  {k}: {json.dumps(values[k])}\n' for k in FONT_KEYS)+text[block.end(1):])
    used={Path(values['file']).name,Path(values['heading_file']).name}
    for font in (root/'static/fonts').glob('*.woff2'):
        if font.name not in used:
            font.unlink()
            stem=font.name.replace('-latin-variable.woff2','')
            (root/'static/fonts'/('OFL.txt' if stem=='inter' else f'OFL-{stem}.txt')).unlink(missing_ok=True)

def apply_preset(destination, slug, name):
    """Select pages and remove workshop and unrelated example content in a new copy."""
    import shutil
    root=Path(destination)
    source=root/'data/presets'/f'{slug}.json'
    profile=read(source)
    original_name=profile['name']
    def rename(value):
        if isinstance(value,str): return value.replace(original_name,name)
        if isinstance(value,list): return [rename(item) for item in value]
        if isinstance(value,dict): return {key:rename(item) for key,item in value.items()}
        return value
    profile=rename(profile)
    profile['name']=name
    # Approvals belong to the business that confirmed them; a copy starts with none.
    profile.pop('approved_claims',None)
    profile.pop('claim_evidence',None)
    for preset in (root/'data/presets').glob('*.json'):
        if preset!=source: preset.unlink()
    selected={s['content'] for page in profile['pages'].values() for s in page['sections']}
    profile['sections']={k:v for k,v in profile['sections'].items() if k in selected}
    source.write_text(json.dumps(profile,indent=2,ensure_ascii=False)+'\n')
    (root/'data/factory.json').write_text(json.dumps(dict(preset=slug,workshop=False),indent=2)+'\n')
    (root/'data/examples.json').unlink(missing_ok=True)
    for path in (root/'content').iterdir():
        if path.is_dir() and path.name not in profile['pages']: shutil.rmtree(path)
    for key,page in profile['pages'].items():
        path=root/'content'/('_index.md' if key=='home' else f'{key}/_index.md')
        path.parent.mkdir(parents=True,exist_ok=True)
        # The preset's own page description is the authoritative one; head.html, llms.txt and the
        # sitemap all read it from here. Only fall back to sample wording when the preset omits it.
        description=(page.get('description') or '').strip() or f"{name}: {page['title'].lower()} and sample information. Content awaits business review."
        path.write_text(json.dumps(dict(title=page['title'],description=description),indent=2)+'\n')
    prune_unlinked_details(root/'content', profile)
    # Structured contact choices follow the selected business instead of the agency demo.
    # Project types come from the preset's services section at render time, so only budgets are written here.
    (root/'data/contact.yaml').write_text(json.dumps(dict(budgets=['To be discussed','I have a scope in mind'],budget_help='No sample budget is a quote.'),indent=2)+'\n')
    site=root/'data/site.yaml';text=site.read_text()
    navigation=[dict(label=p['title'],url='/' if k=='home' else '/'+k+'/') for k,p in profile['pages'].items()]
    text=replace_block(text,'navigation',navigation)
    values=dict(notice='Preview · Content awaiting review',description=(profile.get('description') or '').strip() or f'{name}: sample business website. Content awaits review.',tagline=profile['label'],address='Example business · Details awaiting confirmation',email='hello@example.invalid',hours='Hours to be confirmed',location='Service location to be confirmed')
    for key,value in values.items(): text=re.sub(r'^'+key+r':.*$',lambda _:key+': '+json.dumps(value),text,flags=re.M)
    # Remove agency-specific footer/legacy copy from the client source.
    text=replace_block(text,'cta',dict(label='Your next step',heading='Let’s talk about what you need.'))
    # The master's search-engine business details (type, city) belong to the master's business.
    text=replace_block(text,'organization',dict(type='Organization'))
    text=replace_block(text,'social',dict(heading=name,caption='Fictional preview · Content awaiting review'))
    accent = read(root/'data/tones.json')[profile['tone']]
    text=re.sub(r'^  accent:.*$', '  accent: '+json.dumps(accent),text,flags=re.M)
    primary = next((profile['sections'][s['content']].get('action') for s in profile['pages']['home']['sections']
                    if profile['sections'][s['content']].get('action')), None)
    if primary:
        text=replace_block(text,'primary_cta',primary)
    elif 'estimate' in profile['pages']:
        text=replace_block(text,'primary_cta',dict(label='Build a project brief',url='/estimate/'))
    else:
        text=replace_block(text,'primary_cta',dict(label='Explore',url='/'))
    site.write_text(text)
    # Asset references live in the preset *and* in the detail pages that survived pruning, whose
    # front matter names its own artwork. Scanning only the preset deleted images that a retained
    # page still rendered, which failed the build instead of the validation.
    referenced_images = referenced_assets(profile, root/'content')
    for stem in ('fieldwork','forma','common-ground','northline'):
        if f'images/{stem}.png' not in referenced_images:
            (root/'assets/images'/f'{stem}.png').unlink(missing_ok=True)
    construction_images = root/'assets/images/construction'
    if construction_images.is_dir():
        for image in construction_images.rglob('*'):
            if image.is_file() and image.relative_to(root/'assets').as_posix() not in referenced_images:
                image.unlink()
        if not any(construction_images.rglob('*')):
            shutil.rmtree(construction_images, ignore_errors=True)

if __name__=='__main__':
    import sys
    errors=validate()
    if '--json' in sys.argv[1:]:
        from report import emit
        sys.exit(emit(errors))
    if errors: print('\n'.join(errors),file=sys.stderr)
    else: print('Factory configuration passed: content, variants, dependencies, page links, and assets.')
    sys.exit(bool(errors))
