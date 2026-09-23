#!/usr/bin/env python3
"""Convert a website project plan from the planner into a validated renderer preset."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from factory import validate

# Missing facts are marked, never invented: every generated placeholder carries this text so
# it is easy to find and replace before anything is published.
TBC = 'To be confirmed'

# The planner (assets/js/workflow.js) labels eight core modules with these names and every
# other module with its registry name. Keep this map identical to `legacy` in workflow.js;
# scripts/test_from_plan.py checks that it is.
PLANNER_LABELS = {'hero': 'Introduction', 'services': 'Services', 'about': 'About', 'work': 'Proof',
                  'process': 'Process', 'faq': 'FAQ', 'contact': 'Contact', 'cta': 'Call to action'}

def module_names(registry):
    """Map every name a plan may use for a section (planner label or registry key) to its module."""
    names = {key: key for key in registry}
    names.update({PLANNER_LABELS.get(key, value['name']): key for key, value in registry.items()})
    return names

def slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or 'page'

def parse_items(text, default_title="Detail"):
    # Strip list markers ("- ", "* ", "• ", "1. ", "2) ") only, so "24/7 support" keeps its digits.
    lines = [re.sub(r'^(?:[-*•]|\d+[.)])\s+', '', line.strip()) for line in (text or '').splitlines() if line.strip()]
    if not lines:
        return [{"title": f"{default_title} {TBC.lower()}", "text": f"{TBC}: add confirmed details before publishing."}]
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
    names = module_names(registry)
    unknown = sorted({str(s.get('kind') or '(missing)') for p in project.get('pages', []) for s in p.get('sections', [])
                      if s.get('kind') not in names})
    if unknown:
        raise ValueError('Unknown section types: ' + ', '.join(unknown)
                         + '. Use a planner section name or a module key from data/modules.json.')
    
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
        if p_slug in page_map:
            raise ValueError(f'Two pages would share the address /{p_slug}/. Rename one of them.')
        page_map[p_slug] = dict(p, sections=[dict(s, kind=names[s['kind']]) for s in p.get('sections', [])])

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
                {'kind': 'contact', 'title': 'Contact details', 'body': f'{TBC}: contact hours and details.'}
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
            'title': 'Services',
            'body': f'Services {TBC.lower()}: list the services this business actually offers.'
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
        if not raw_sections or raw_sections[0].get('kind') != 'hero':
            raw_sections.insert(0, {
                'kind': 'hero',
                'variant': 'compact' if p_slug != 'home' else 'split',
                'title': p_title,
                'body': p_desc
            })

        for idx, s in enumerate(raw_sections):
            kind = s['kind']

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
                    items = [{"title": str(it.get('title') or f'Item {TBC.lower()}'), "text": str(it.get('text') or TBC),
                              **{k: str(it[k]) for k in item_req if it.get(k)}} for it in s['items']]
                else:
                    items = parse_items(s.get('body'), default_title=kind.capitalize())
                
                # Fill special item requirements
                for it in items:
                    for field, choices in mod_meta.get('item_choices', {}).items():
                        # A classification such as included/excluded is a business decision,
                        # so it is never guessed.
                        if it.get(field) not in choices:
                            raise ValueError(f'{p_title} / {kind}: item "{it["title"]}" needs {field} set to one of: '
                                             + ', '.join(choices) + '. Give the section an "items" list that sets it.')
                    if 'value' in item_req:
                        it.setdefault('value', TBC)
                    if 'when' in item_req:
                        it.setdefault('when', TBC)
                    if 'place' in item_req:
                        it.setdefault('place', TBC)
                    if 'url' in item_req:
                        it.setdefault('url', '/contact/')
                        it.setdefault('link_label', 'Enquire')
                    if kind == 'comparison':
                        it.setdefault('scope', TBC)
                        it.setdefault('best', TBC)
                content_block['items'] = items

            if 'notice' in req_fields:
                content_block['notice'] = (s.get('notice') or s.get('a11y') or f"{TBC}: details agreed in the project brief.").strip()

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

    try:
        slug, preset = convert_plan_to_preset(plan_data, registry)
    except ValueError as error:
        parser.error(str(error))
    if args.name:
        slug = slugify(args.name)

    # Validate against factory rules in-memory
    errors = validate(ROOT, extra_presets={slug: preset})
    if errors:
        print("Validation errors in generated preset:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.write:
        target_preset_path = ROOT / 'data/presets' / f"{slug}.json"
        if target_preset_path.exists() and not args.force:
            parser.error(f'{target_preset_path.relative_to(ROOT)} already exists. Choose another --name, '
                         'or add --force to replace it.')
        temp_target = target_preset_path.with_suffix('.tmp.json')
        temp_target.write_text(json.dumps(preset, indent=2) + '\n')
        temp_target.replace(target_preset_path)
        print(f"Preset successfully compiled and verified: {target_preset_path}")
    else:
        print(json.dumps(preset, indent=2))
    placeholders = json.dumps(preset).count(TBC)
    if placeholders:
        print(f'Note: {placeholders} field(s) say "{TBC}". Replace them with real business facts before publishing.',
              file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())
