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

MAX_PARSED_ITEMS = 8

def parse_items(text, default_title="Detail", where=''):
    # Strip list markers ("- ", "* ", "• ", "1. ", "2) ") only, so "24/7 support" keeps its digits.
    lines = [re.sub(r'^(?:[-*•]|\d+[.)])\s+', '', line.strip()) for line in (text or '').splitlines() if line.strip()]
    if not lines:
        return [{"title": f"{default_title} {TBC.lower()}", "text": f"{TBC}: add confirmed details before publishing."}]
    if len(lines) > MAX_PARSED_ITEMS:
        raise ValueError(f'{where or default_title}: {len(lines)} lines of section copy would become items, but '
                         f'only {MAX_PARSED_ITEMS} are kept. Shorten the copy, or give the section an "items" '
                         'list so every entry is carried deliberately.')
    items = []
    for i, line in enumerate(lines[:MAX_PARSED_ITEMS]):
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

def starter_reference(project):
    """What the starter a plan came from still knows, for backups that predate carrying it.

    Older exports kept only display titles, so a link written against the original page key
    (/estimate/) matched nothing once "Project brief" became /project-brief/, and a field the
    planner has no editor for (the brief builder's service list) was simply absent. Both are
    recovered from the recorded starter's own content, never guessed, and an unrecognised starter
    yields nothing. Returns (display title -> page key, (page key, module) -> content block,
    (page key, module) -> anchor).

    ponytail: keyed by page and module, so the first of two same-module sections on one page wins.
    Key on the section's position as well if a starter ever needs two of the same module."""
    slug = str(project.get('starterPreset') or '').strip()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', slug):
        return {}, {}, {}
    source = ROOT / 'data/presets' / f'{slug}.json'
    if not source.is_file():
        return {}, {}, {}
    try:
        profile = json.loads(source.read_text())
    except (ValueError, OSError):
        return {}, {}, {}
    pages = profile.get('pages', {})
    sections = profile.get('sections', {})
    keys = {str(page.get('title', '')).strip(): key for key, page in pages.items() if page.get('title')}
    content, anchors = {}, {}
    for key, page in pages.items():
        for spec in page.get('sections', []) or []:
            found = sections.get(spec.get('content'))
            if isinstance(found, dict):
                content.setdefault((key, spec.get('module')), found)
            if spec.get('anchor'):
                anchors.setdefault((key, spec.get('module')), str(spec['anchor']))
    return keys, content, anchors

def action_url(target, page_slugs, fallback, where):
    """The destination a plan asked for, or `fallback` when it named none.

    A planned destination is never quietly replaced: an internal path that no page answers, or an
    address this compiler cannot represent, stops the build instead of redirecting the visitor
    somewhere the plan did not choose."""
    target = (target or '').strip()
    if not target:
        return fallback
    if target.startswith(('http://', 'https://', 'mailto:', 'tel:')):
        return target
    if target.startswith('#'):
        return target
    if not target.startswith('/'):
        raise ValueError(f'{where}: action destination {target!r} is not a usable address. Use a path '
                         'like /services/, an #anchor, or a full https:// URL.')
    page = re.split(r'[#?]', target, 1)[0]
    slug = page.strip('/').split('/')[0]
    if slug and slug not in page_slugs:
        raise ValueError(f'{where}: action destination {target!r} points at /{slug}/, which this plan has '
                         'no page for. Add that page or change the destination.')
    return target

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
    recovered, starter_content, starter_anchors = starter_reference(project)
    page_map = {}
    for p in raw_pages:
        p_name = p.get('name', 'Page').strip()
        # A plan that carries its own page key keeps it, so a route never changes because the
        # display title did. Only pages without one are named after their title.
        carried = str(p.get('slug') or '').strip() or recovered.get(p_name, '')
        if carried and not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', carried):
            raise ValueError(f'Page "{p_name}" has an unusable page key {carried!r}. '
                             'Use lowercase letters, digits, and hyphens.')
        p_slug = carried or ('home' if p_name.lower() in ('home', 'index', 'welcome') else slugify(p_name))
        if p_slug in page_map:
            raise ValueError(f'Two pages would share the address /{p_slug}/. Rename one of them.')
        page_map[p_slug] = dict(p, sections=[dict(s, kind=names[s['kind']]) for s in p.get('sections', [])])
    plan_order = list(page_map)

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

    # Keep the order the plan gave, with home first because it is the site root. Pages the
    # compiler added itself go last; it must not silently reshuffle a navigation someone chose.
    added = [s for s in page_map if s not in plan_order]
    ordered_slugs = (['home'] if 'home' in page_map else []) \
        + [s for s in plan_order if s != 'home'] \
        + [s for s in added if s != 'home']
    
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
            spec = {
                "module": kind,
                "variant": variant,
                "content": content_key
            }
            anchor = str(s.get('anchor') or starter_anchors.get((p_slug, kind), '')).strip()
            if anchor:
                if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', anchor):
                    raise ValueError(f'{p_title} / {kind}: anchor {anchor!r} is not usable. Use lowercase '
                                     'letters, digits, and hyphens.')
                spec['anchor'] = anchor
            page_sections.append(spec)

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
                fallback = "/contact/" if "contact" in ordered_slugs else "/"
                content_block['action'] = {
                    "label": (s.get('cta') or "Get in touch").strip(),
                    "url": action_url(s.get('target'), ordered_slugs, fallback, f'{p_title} / {kind}')
                }

            if 'items' in req_fields:
                source_items = s.get('items') if isinstance(s.get('items'), list) and s['items'] else None
                if source_items is None:
                    # A backup from before the planner carried items holds only the prose those
                    # items were rendered into, mixed in with the section intro and notes. When
                    # every starter item title is still present, the body is unedited starter copy,
                    # so the structure it came from is recovered instead of re-parsed out of prose.
                    known = starter_content.get((p_slug, kind), {}).get('items') or []
                    titles = [str(x.get('title', '')).strip() for x in known if isinstance(x, dict)]
                    body_text = s.get('body') or ''
                    if titles and all(title and title in body_text for title in titles):
                        source_items = known
                if source_items is not None:
                    items = [{"title": str(it.get('title') or f'Item {TBC.lower()}'), "text": str(it.get('text') or TBC),
                              **{k: str(it[k]) for k in item_req if it.get(k)}} for it in source_items]
                else:
                    items = parse_items(s.get('body'), default_title=kind.capitalize(), where=f'{p_title} / {kind}')
                
                # A classification the starter already made can be recovered by title, for backups
                # written before the planner carried structured items. Anything the plan itself
                # says wins, and a retitled item finds no match and still stops the build.
                from_starter = {str(x.get('title', '')).strip(): x
                                for x in starter_content.get((p_slug, kind), {}).get('items', []) or []
                                if isinstance(x, dict)}
                # Fill special item requirements
                for it in items:
                    for field, choices in mod_meta.get('item_choices', {}).items():
                        # A classification such as included/excluded is a business decision,
                        # so it is never guessed.
                        if it.get(field) not in choices:
                            known = from_starter.get(it['title'], {}).get(field)
                            if known in choices:
                                it[field] = known
                                continue
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

            if 'services' in req_fields:
                planned = s.get('services') or starter_content.get((p_slug, kind), {}).get('services') or []
                services = [str(x).strip() for x in planned if str(x).strip()]
                if not services:
                    raise ValueError(f'{p_title} / {kind}: this section needs a "services" list naming the '
                                     'services a visitor can choose. It is a business decision, so it is '
                                     'never generated.')
                content_block['services'] = services

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
        # A hidden .tmp name: an interrupted write can never be read as a preset by *.json globs.
        temp_target = target_preset_path.with_name(f'.{slug}.json.tmp')
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
