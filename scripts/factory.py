#!/usr/bin/env python3
"""Validate and scaffold the declarative website factory using only the standard library."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())

def validate(root=ROOT, workshop=None):
    errors = []
    try:
        config = read(root / 'data/factory.json')
        if workshop is not None:
            config['workshop'] = workshop
        registry = read(root / 'data/modules.json')
        profiles = {p.stem: read(p) for p in (root / 'data/presets').glob('*.json')}
        examples = read(root / 'data/examples.json') if config.get('workshop') else {}
    except (OSError, ValueError) as error:
        return [str(error)]
    if config.get('preset') not in profiles:
        errors.append('data/factory.json: unknown selected preset')
    if type(config.get('workshop')) is not bool:
        errors.append('data/factory.json: workshop must be true or false')
    def check_content(module, content, label, profile=None):
        if not isinstance(content, dict):
            errors.append(f'{label}: content must be an object'); return
        for field in registry[module]['required']:
            if not content.get(field): errors.append(f'{label}: missing required field {field}')
        for field in ('title','intro','body','notice','label','aside','note'):
            if field in content and not isinstance(content[field], str): errors.append(f'{label}: {field} must be text')
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
        for field in ('action','secondary'):
            if field in content and (not isinstance(content[field],dict) or not content[field].get('label') or not content[field].get('url')):
                errors.append(f'{label}: {field} needs label and url')
        def links(value):
            if isinstance(value,dict):
                for key, val in value.items():
                    if key=='url':
                        if not isinstance(val,str): errors.append(f'{label}: URL must be text'); continue
                        parsed=urlsplit(val)
                        if parsed.scheme or parsed.netloc or not val.startswith('/') or '..' in parsed.path.split('/') or parsed.query or parsed.fragment:
                            errors.append(f'{label}: module links must be local page paths: {val}'); continue
                        parts=parsed.path.strip('/').split('/')
                        page=parts[0] or 'home'
                        if profile and page not in profile['pages']:
                            errors.append(f'{label}: link to omitted page {val}')
                        path=root/'content'/parsed.path.strip('/')
                        if page!='home' and not any(p.is_file() for p in [path/'_index.md',path/'index.md',path.with_suffix('.md')]):
                            errors.append(f'{label}: link has no content page: {val}')
                    else: links(val)
            elif isinstance(value,list):
                for item in value: links(item)
        links(content)
    for slug, profile in profiles.items():
        if not re.fullmatch(r'[a-z][a-z0-9-]*',slug): errors.append(f'Invalid preset identifier {slug}')
        if profile.get('tone') not in ('yellow','clay','sage','blue'): errors.append(f'{slug}: unknown tone')
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
            sections=page.get('sections')
            if not isinstance(sections,list) or not sections:
                errors.append(f'{slug}/{key}: sections must be a nonempty list'); continue
            if not all(page.get(k) for k in ('title','description')): errors.append(f'{slug}/{key}: title and description required')
            if sections[0].get('module')!='hero' or sum(s.get('module')=='hero' for s in sections)!=1:
                errors.append(f'{slug}/{key}: exactly one hero must be first')
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
    # Structured contact choices follow the selected business instead of the agency demo.
    # Project types come from the preset's services section at render time, so only budgets are written here.
    (root/'data/contact.yaml').write_text(json.dumps(dict(budgets=['To be discussed','I have a scope in mind'],budget_help='No sample budget is a quote.'),indent=2)+'\n')
    site=root/'data/site.yaml';text=site.read_text()
    navigation=[dict(label=p['title'],url='/' if k=='home' else '/'+k+'/') for k,p in profile['pages'].items()]
    text=re.sub(r'^navigation:\n(?:[ \t].*\n)*', lambda _: 'navigation: '+json.dumps(navigation)+'\n',text,flags=re.M)
    values=dict(description=f'{name}: sample business website. Content awaits review.',tagline=profile['label'],address='Example business · Details awaiting confirmation',email='hello@example.invalid',hours='Hours to be confirmed',location='Service location to be confirmed')
    for key,value in values.items(): text=re.sub(r'^'+key+r':.*$',lambda _:key+': '+json.dumps(value),text,flags=re.M)
    # Remove agency-specific footer/legacy copy from the client source.
    text=re.sub(r'^cta:\n(?:[ \t].*\n)*',lambda _: 'cta: '+json.dumps(dict(label='Your next step',heading='Let’s talk about what you need.'))+'\n',text,flags=re.M)
    text=re.sub(r'^social:\n(?:[ \t].*\n)*',lambda _: 'social: '+json.dumps(dict(heading=name,caption='Fictional preview · Content awaiting review'))+'\n',text,flags=re.M)
    accent = {'yellow':'#ffc400','clay':'#edb08e','sage':'#b9d7bb','blue':'#a6cef7'}[profile['tone']]
    text=re.sub(r'^  accent:.*$', '  accent: '+json.dumps(accent),text,flags=re.M)
    site.write_text(text)
    if 'work' not in profile['pages']:
        for stem in ('fieldwork','forma','common-ground','northline'):
            (root/'assets/images'/f'{stem}.png').unlink(missing_ok=True)

if __name__=='__main__':
    import sys
    errors=validate()
    if errors: print('\n'.join(errors),file=sys.stderr)
    else: print('Factory configuration passed: content, variants, dependencies, page links, and assets.')
    sys.exit(bool(errors))
