#!/usr/bin/env python3
"""Validate and scaffold the declarative website factory using only the standard library."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

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
    try:
        config = read(root / 'data/factory.json')
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
    if config.get('preset') not in profiles:
        errors.append('data/factory.json: unknown selected preset')
    if type(config.get('workshop')) is not bool:
        errors.append('data/factory.json: workshop must be true or false')
    # The header, footer, titles, and structured data read data/site.yaml, while the pages read
    # the preset. A mismatch published one business's pages under another's name, so it fails.
    named=re.search(r'(?m)^name:\s*(.+?)\s*$', (root/'data/site.yaml').read_text()) if (root/'data/site.yaml').is_file() else None
    site_name=yaml_scalar(named.group(1)) if named else None
    errors+=font_errors(root)
    if config.get('preset') in profiles and site_name!=profiles[config['preset']].get('name'):
        errors.append(f"data/site.yaml: name {site_name!r} must match the selected preset's name {profiles[config['preset']].get('name')!r}")
    def check_content(module, content, label, profile=None):
        if not isinstance(content, dict):
            errors.append(f'{label}: content must be an object'); return
        for field in registry[module]['required']:
            if not content.get(field): errors.append(f'{label}: missing required field {field}')
        for field in ('title','intro','body','notice','label','aside','note','image','imageAlt'):
            if field in content and not isinstance(content[field], str): errors.append(f'{label}: {field} must be text')
        if content.get('image'):
            image = Path(content['image'])
            if image.is_absolute() or '..' in image.parts or not (root/'assets'/image).is_file():
                errors.append(f'{label}: missing or unsafe image {image}')
            if not isinstance(content.get('imageAlt'), str) or not content['imageAlt'].strip():
                errors.append(f'{label}: image needs descriptive imageAlt text')
        if module == 'project-brief':
            options = content.get('services')
            if not isinstance(options, list) or not options or not all(isinstance(option, str) and option.strip() for option in options):
                errors.append(f'{label}: services must be a nonempty list of service names')
            elif len(set(options)) != len(options):
                errors.append(f'{label}: services must not contain duplicates')
            elif profile:
                offered = set()
                for page in profile.get('pages', {}).values():
                    for section in page.get('sections', []) if isinstance(page, dict) else []:
                        if section.get('module') == 'services':
                            data = profile.get('sections', {}).get(section.get('content'), {})
                            offered.update(item.get('title') for item in data.get('items', []) if isinstance(item, dict))
                missing = set(options) - offered
                if missing:
                    errors.append(f'{label}: project brief includes services absent from the site catalog: {", ".join(sorted(missing))}')
        if 'items' in registry[module]['required']:
            if not isinstance(content.get('items'), list) or not content['items']:
                errors.append(f'{label}: items must be a nonempty list'); return
            for i, item in enumerate(content['items']):
                if not isinstance(item, dict) or not all(isinstance(item.get(k),str) and item[k].strip() for k in ('title','text')):
                    errors.append(f'{label}: item {i+1} needs title and text'); continue
                for field in registry[module].get('item_required', []):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        errors.append(f'{label}: item {i+1} needs {field}')
                for field, choices in registry[module].get('item_choices', {}).items():
                    if item.get(field) not in choices:
                        errors.append(f'{label}: item {i+1} has unsupported {field}')
                if module == 'comparison' and not all(item.get(k) for k in ('scope','best')):
                    errors.append(f'{label}: comparison needs scope and best')
                if item.get('image'):
                    image = Path(item['image'])
                    if image.is_absolute() or '..' in image.parts or not (root/'assets'/image).is_file():
                        errors.append(f'{label}: missing or unsafe image {image}')
                    if 'imageAlt' in item and not isinstance(item['imageAlt'], str):
                        errors.append(f'{label}: item {i+1} imageAlt must be text')
        for field in ('action','secondary'):
            if field in content and (not isinstance(content[field],dict) or not content[field].get('label') or not content[field].get('url')):
                errors.append(f'{label}: {field} needs label and url')
        def links(value):
            if isinstance(value,dict):
                for key, val in value.items():
                    if key=='url':
                        if not isinstance(val,str): errors.append(f'{label}: URL must be text'); continue
                        if val.startswith(('mailto:','tel:')):
                            problem=contact_link_error(val)
                            if problem: errors.append(f'{label}: {problem}')
                            continue
                        parsed=urlsplit(val)
                        if parsed.scheme or parsed.netloc or not val.startswith('/') or '..' in parsed.path.split('/') or parsed.query or (parsed.fragment and not ANCHOR.fullmatch(parsed.fragment)):
                            errors.append(f'{label}: module links must be local page paths, mailto:, or tel: {val}'); continue
                        parts=parsed.path.strip('/').split('/')
                        page=parts[0] or 'home'
                        if profile and page not in profile['pages']:
                            errors.append(f'{label}: link to omitted page {val}')
                        elif profile and parsed.fragment and isinstance(profile['pages'][page],dict):
                            # A deep link must land on a section that declares that anchor.
                            declared={s.get('anchor') for s in profile['pages'][page].get('sections',[]) if isinstance(s,dict)}
                            if parsed.fragment not in declared:
                                errors.append(f'{label}: link to missing anchor {val}; add "anchor": "{parsed.fragment}" to a section on that page')
                        path=root/'content'/parsed.path.strip('/')
                        if page!='home' and not any(p.is_file() for p in [path/'_index.md',path/'index.md',path.with_suffix('.md')]):
                            errors.append(f'{label}: link has no content page: {val}')
                    else: links(val)
            elif isinstance(value,list):
                for item in value: links(item)
        links(content)
    for slug, profile in profiles.items():
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug): errors.append(f'Invalid preset identifier {slug}')
        approved=profile.get('approved_claims',[])
        if not isinstance(approved,list) or not all(isinstance(a,str) and a.strip() for a in approved):
            errors.append(f'{slug}: approved_claims must be a list of text')
        if profile.get('tone') not in tones: errors.append(f"{slug}: unknown tone; choose one of {', '.join(tones)}")
        if profile.get('palette') and profile['palette'] not in palettes:
            errors.append(f"{slug}: unknown palette; choose one of {', '.join(palettes)}")
        if profile.get('font_pairing') and profile['font_pairing'] not in font_pairings:
            errors.append(f"{slug}: unknown font pairing; choose one of {', '.join(font_pairings)}")
        if not isinstance(profile.get('pages'),dict) or not isinstance(profile.get('sections'),dict):
            errors.append(f'{slug}: pages and sections must be objects'); continue
        if not all(k in profile['pages'] for k in ('home','contact')): errors.append(f'{slug}: home and contact are required')
        # The contact form offers the services module's own items as project types, whatever
        # content key it references. Without one there is nothing to offer, so fail here.
        if 'contact' in profile['pages'] and not any(s.get('module')=='services'
                for page in profile['pages'].values() if isinstance(page,dict)
                for s in (page.get('sections') or []) if isinstance(s,dict)):
            errors.append(f'{slug}: a services module is required somewhere; the contact form offers its items as project types')
        for key,page in profile['pages'].items():
            if not re.fullmatch(r'[a-z][a-z0-9-]*',key): errors.append(f'{slug}: invalid page key {key}')
            if not isinstance(page,dict):
                errors.append(f'{slug}/{key}: page must be an object'); continue
            sections=page.get('sections')
            if not isinstance(sections,list) or not sections or not all(isinstance(s,dict) for s in sections):
                errors.append(f'{slug}/{key}: sections must be a nonempty list of objects'); continue
            if not all(page.get(k) for k in ('title','description')): errors.append(f'{slug}/{key}: title and description required')
            if sections[0].get('module')!='hero' or sum(s.get('module')=='hero' for s in sections)!=1:
                errors.append(f'{slug}/{key}: exactly one hero must be first')
            anchors=[s['anchor'] for s in sections if 'anchor' in s]
            for anchor in anchors:
                if not isinstance(anchor,str) or not ANCHOR.fullmatch(anchor) or re.fullmatch(r'.*-\d+',anchor):
                    errors.append(f'{slug}/{key}: anchor {anchor!r} must be lowercase words joined by hyphens, not ending in a number')
            if len(set(map(str,anchors)))!=len(anchors):
                errors.append(f'{slug}/{key}: two sections share an anchor')
            for section in sections:
                module=section.get('module');label=f'{slug}/{key}/{module}'
                if module not in registry:
                    errors.append(f'{label}: unknown module'); continue
                if section.get('variant') not in registry[module]['variants']: errors.append(f'{label}: unknown variant')
                for dependency in registry[module].get('dependencies',[]):
                    if dependency not in profile['pages']: errors.append(f'{label}: requires page {dependency}')
                check_content(module,profile['sections'].get(section.get('content')),label,profile)
    for module,content in examples.items():
        if module not in registry: errors.append(f'Unknown catalog module {module}')
        else: check_content(module,content,f'catalog/{module}')
    return errors

def replace_block(text, key, value):
    """Set a top-level site.yaml key to one-line JSON, whether it is currently a block or already
    one line (a copy can be re-sculpted with another preset, which runs this twice)."""
    return re.sub(r'^'+key+r':(?:[ \t]*\n(?:[ \t]+.*\n)*|[ \t]+\S.*\n)', lambda _: key+': '+json.dumps(value)+'\n', text, flags=re.M)

def prune_unlinked_details(content_root, profile):
    """Keep detail pages only when a selected composition links to them."""
    linked = {
        item.get('url')
        for section in profile.get('sections', {}).values() if isinstance(section, dict)
        for item in section.get('items', []) if isinstance(item, dict) and isinstance(item.get('url'), str)
    }
    for section in ('services', 'work'):
        directory = Path(content_root) / section
        if not directory.is_dir():
            continue
        for page in directory.glob('*.md'):
            if page.name != '_index.md' and f'/{section}/{page.stem}/' not in linked:
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
        path.write_text(json.dumps(dict(title=page['title'],description=f"{name}: {page['title'].lower()} and sample information. Content awaits business review."),indent=2)+'\n')
    prune_unlinked_details(root/'content', profile)
    # Structured contact choices follow the selected business instead of the agency demo.
    # Project types come from the preset's services section at render time, so only budgets are written here.
    (root/'data/contact.yaml').write_text(json.dumps(dict(budgets=['To be discussed','I have a scope in mind'],budget_help='No sample budget is a quote.'),indent=2)+'\n')
    site=root/'data/site.yaml';text=site.read_text()
    navigation=[dict(label=p['title'],url='/' if k=='home' else '/'+k+'/') for k,p in profile['pages'].items()]
    text=replace_block(text,'navigation',navigation)
    values=dict(notice='Preview · Content awaiting review',description=f'{name}: sample business website. Content awaits review.',tagline=profile['label'],address='Example business · Details awaiting confirmation',email='hello@example.invalid',hours='Hours to be confirmed',location='Service location to be confirmed')
    for key,value in values.items(): text=re.sub(r'^'+key+r':.*$',lambda _:key+': '+json.dumps(value),text,flags=re.M)
    # Remove agency-specific footer/legacy copy from the client source.
    text=replace_block(text,'cta',dict(label='Your next step',heading='Let’s talk about what you need.'))
    # The master's search-engine business details (type, city) belong to the master's business.
    text=replace_block(text,'organization',dict(type='Organization'))
    text=replace_block(text,'social',dict(heading=name,caption='Fictional preview · Content awaiting review'))
    accent = read(root/'data/tones.json')[profile['tone']]
    text=re.sub(r'^  accent:.*$', '  accent: '+json.dumps(accent),text,flags=re.M)
    if 'estimate' in profile['pages']:
        text=replace_block(text,'primary_cta',dict(label='Build a project brief',url='/estimate/'))
    site.write_text(text)
    referenced_images = set()
    for content in profile['sections'].values():
        if isinstance(content, dict):
            if isinstance(content.get('image'), str): referenced_images.add(content['image'])
            for item in content.get('items', []):
                if isinstance(item, dict) and isinstance(item.get('image'), str):
                    referenced_images.add(item['image'])
    for stem in ('fieldwork','forma','common-ground','northline'):
        name=f'images/{stem}.png'
        if name not in referenced_images:
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
