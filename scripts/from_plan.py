#!/usr/bin/env python3
"""Convert a website project plan from the planner into a validated renderer preset."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from factory import validate

# Every value the plan did not supply carries this marker, so no invented fact
# (a price, a date, a place, a service claim) can pass as approved copy.
TO_CONFIRM = 'To confirm with the client.'

def placeholders(preset):
    """List the content keys that still contain unconfirmed placeholder copy."""
    return sorted(key for key, block in preset['sections'].items() if TO_CONFIRM in json.dumps(block))

def slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or 'page'

def parse_items(text, default_title="Detail"):
    lines = [line.strip().lstrip('-*•0123456789. ') for line in (text or '').splitlines() if line.strip()]
    if not lines:
        return [
            {"title": f"{default_title} 1", "text": TO_CONFIRM},
            {"title": f"{default_title} 2", "text": TO_CONFIRM}
        ]
    items = []
    for i, line in enumerate(lines[:8]):
        if ' - ' in line:
            parts = line.split(' - ', 1)
            items.append({"title": parts[0].strip(), "text": parts[1].strip()})
        elif ': ' in line:
            parts = line.split(': ', 1)
            items.append({"title": parts[0].strip(), "text": parts[1].strip()})
        elif ':' in line:
            parts = line.split(':', 1)
            items.append({"title": parts[0].strip() or f"{default_title} {i+1}", "text": parts[1].strip() or line})
        else:
            items.append({"title": f"{default_title} {i+1}", "text": line})
    return items

def convert_plan_to_preset(project_data, registry):
    # Support both full backup export {"version":1,"projects":[...]} and direct project object
    project = project_data['projects'][0] if 'projects' in project_data else project_data
    
    preset_name = project.get('name', 'Untitled Website').strip()
    slug = slugify(preset_name)
    
    preset = {
        "name": preset_name,
        "label": project.get('business', preset_name).strip() or "Digital studio",
        "tone": project.get('tone', 'yellow'),
        "description": project.get('goal', project.get('scope', 'A high-performance small-business website.')).strip(),
        "pages": {},
        "sections": {}
    }

    # Normalize pages
    raw_pages = project.get('pages', [])
    page_map = {}
    for p in raw_pages:
        p_name = p.get('name', 'Page').strip()
        p_slug = 'home' if p_name.lower() in ('home', 'index', 'welcome') else slugify(p_name)
        page_map[p_slug] = p

    # Ensure required pages: home and contact
    if 'home' not in page_map:
        page_map['home'] = {
            'name': 'Home',
            'purpose': 'Clear promise and high-converting introduction.',
            'sections': [{'kind': 'hero', 'title': preset_name, 'body': preset['description']}]
        }
    if 'contact' not in page_map:
        page_map['contact'] = {
            'name': 'Contact',
            'purpose': 'Direct enquiry path for new client projects.',
            'sections': [
                {'kind': 'hero', 'variant': 'compact', 'title': 'Get in touch', 'body': 'Start a project conversation.'},
                {'kind': 'contact', 'title': 'Contact details', 'body': TO_CONFIRM}
            ]
        }

    # Ensure services module exists across the preset
    has_services = any(
        s.get('kind') == 'services'
        for pg in page_map.values()
        for s in pg.get('sections', [])
    )
    if not has_services:
        page_map['home'].setdefault('sections', []).append({
            'kind': 'services',
            'variant': 'cards',
            'title': 'Core services',
            'body': ''
        })

    # Order pages with home first, contact last
    ordered_slugs = ['home'] + [s for s in sorted(page_map.keys()) if s not in ('home', 'contact')] + ['contact']
    
    for p_slug in ordered_slugs:
        pg = page_map[p_slug]
        p_title = pg.get('name', p_slug.replace('-', ' ').title()).strip()
        p_desc = pg.get('purpose', f'{p_title} page for {preset_name}.').strip()

        raw_sections = pg.get('sections', [])
        page_sections = []

        # Rule: exactly one hero first
        has_hero = any(s.get('kind') == 'hero' for s in raw_sections)
        if not raw_sections or raw_sections[0].get('kind') != 'hero':
            raw_sections.insert(0, {
                'kind': 'hero',
                'variant': 'compact' if p_slug != 'home' else 'split',
                'title': p_title,
                'body': p_desc
            })

        for idx, s in enumerate(raw_sections):
            kind = s.get('kind', 'hero')
            if kind not in registry:
                continue

            # Exactly one hero per page
            if kind == 'hero' and idx > 0:
                kind = 'cta'

            mod_meta = registry[kind]
            allowed_variants = mod_meta.get('variants', ['default'])
            variant = s.get('variant')
            if variant not in allowed_variants:
                variant = allowed_variants[0]

            content_key = f"{p_slug}-{kind}-{idx+1}"
            page_sections.append({
                "module": kind,
                "variant": variant,
                "content": content_key
            })

            # Build content block adhering to registry schema
            req_fields = mod_meta.get('required', [])
            item_req = mod_meta.get('item_required', [])

            content_block = {
                "title": (s.get('title') or kind.replace('-', ' ').title()).strip()
            }

            if 'intro' in req_fields or 'body' in req_fields:
                intro_text = s.get('body', '').strip() or p_desc
                if 'intro' in req_fields:
                    content_block['intro'] = intro_text
                if 'body' in req_fields:
                    content_block['body'] = intro_text

            if 'action' in req_fields:
                content_block['action'] = {
                    "label": (s.get('cta') or "Get in touch").strip(),
                    "url": "/contact/" if "contact" in ordered_slugs else "/"
                }

            if 'items' in req_fields:
                if isinstance(s.get('items'), list) and s['items']:
                    items = [{"title": str(it.get('title') or 'Item'), "text": str(it.get('text') or TO_CONFIRM)} for it in s['items']]
                else:
                    items = parse_items(s.get('body'), default_title=kind.capitalize())
                
                # Fill special item requirements
                for it in items:
                    if 'group' in item_req:
                        it.setdefault('group', 'Core')
                    if 'value' in item_req:
                        it.setdefault('value', TO_CONFIRM)
                    if 'when' in item_req:
                        it.setdefault('when', TO_CONFIRM)
                    if 'place' in item_req:
                        it.setdefault('place', TO_CONFIRM)
                    if 'url' in item_req:
                        it.setdefault('url', '/contact/')
                        it.setdefault('link_label', 'Enquire')
                    if kind == 'comparison':
                        it.setdefault('scope', TO_CONFIRM)
                        it.setdefault('best', TO_CONFIRM)
                content_block['items'] = items

            if 'notice' in req_fields:
                content_block['notice'] = (s.get('notice') or s.get('a11y') or TO_CONFIRM).strip()

            preset['sections'][content_key] = content_block

        preset['pages'][p_slug] = {
            "title": p_title,
            "description": p_desc,
            "sections": page_sections
        }

    return slug, preset

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', help='Path to planner JSON export file')
    parser.add_argument('--name', help='Override preset identifier/slug')
    parser.add_argument('--write', action='store_true', help='Save preset directly to data/presets/<slug>.json')
    parser.add_argument('--force', action='store_true', help='With --write, replace an existing preset of the same name')
    args = parser.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.is_file():
        parser.error(f'File not found: {plan_path}')

    registry = json.loads((ROOT / 'data/modules.json').read_text())
    plan_data = json.loads(plan_path.read_text())

    slug, preset = convert_plan_to_preset(plan_data, registry)
    if args.name:
        slug = slugify(args.name)

    target = ROOT / 'data/presets' / f"{slug}.json"
    if args.write and target.exists() and not args.force:
        parser.error(f'{target.relative_to(ROOT)} already exists. Choose another --name, or pass --force to replace it.')

    # Validate against the factory rules in a scratch copy of data/, so a preview or a
    # failed compile never writes, replaces, or deletes a real preset.
    with tempfile.TemporaryDirectory(prefix='from-plan-') as scratch:
        scratch = Path(scratch)
        shutil.copytree(ROOT / 'data', scratch / 'data')
        for folder in ('assets', 'content'):
            (scratch / folder).symlink_to(ROOT / folder, target_is_directory=True)
        (scratch / 'data/presets' / f"{slug}.json").write_text(json.dumps(preset, indent=2) + '\n')
        errors = validate(scratch)
    if errors:
        print("Validation errors in generated preset:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    pending = placeholders(preset)
    if pending:
        print(f"Needs client copy before review ({len(pending)} sections contain '{TO_CONFIRM}'): " + ', '.join(pending), file=sys.stderr)
    if args.write:
        target.write_text(json.dumps(preset, indent=2) + '\n')
        print(f"Preset compiled and verified: {target}")
    else:
        print(json.dumps(preset, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
