#!/usr/bin/env python3
"""Tests for scripts/from_plan.py planner-to-preset converter."""
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
from from_plan import convert_plan_to_preset, parse_items, PLANNER_LABELS, TBC
from factory import validate

class FromPlanTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / 'data/modules.json').read_text())

    def test_convert_minimal_plan_produces_valid_preset(self):
        plan = {
            "name": "Oak & Iron",
            "business": "Handcrafted Furniture",
            "goal": "Showcase furniture and take custom commission requests",
            "pages": [
                {
                    "name": "Home",
                    "purpose": "First impression and featured furniture collections",
                    "sections": [
                        {
                            "kind": "hero",
                            "variant": "centered",
                            "title": "Furniture made to endure generations",
                            "body": "Solid hardwood tables, credenzas, and custom architectural woodwork.",
                            "cta": "Request commission",
                            "target": "/contact/"
                        },
                        {
                            "kind": "services",
                            "variant": "cards",
                            "title": "What we build",
                            "body": "Dining tables: Custom slab and joinery tables.\nStorage: Credenzas and built-in shelving.\nRestoration: Heritage furniture preservation."
                        }
                    ]
                }
            ]
        }
        slug, preset = convert_plan_to_preset(plan, self.registry)
        self.assertEqual(slug, "oak-iron")
        self.assertIn("home", preset["pages"])
        self.assertIn("contact", preset["pages"])
        self.assertTrue(any(s["module"] == "services" for pg in preset["pages"].values() for s in pg["sections"]))
        
        # Test validation against factory rules in-memory
        errors = validate(ROOT, extra_presets={slug: preset})
        self.assertEqual(errors, [], f"Validation failed with: {errors}")

    def test_convert_plan_with_missing_hero_and_services(self):
        plan = {
            "name": "Quick Site",
            "pages": [
                {
                    "name": "Home",
                    "sections": [
                        {
                            "kind": "about",
                            "title": "About us",
                            "body": "We are a local team."
                        }
                    ]
                }
            ]
        }
        slug, preset = convert_plan_to_preset(plan, self.registry)
        home_sections = preset["pages"]["home"]["sections"]
        self.assertEqual(home_sections[0]["module"], "hero", "First section on every page must be hero")
        
        # Test validation against factory rules in-memory
        errors = validate(ROOT, extra_presets={slug: preset})
        self.assertEqual(errors, [], f"Validation failed with: {errors}")

    def test_preview_colliding_slug_preserves_existing_preset(self):
        import hashlib
        import subprocess

        # Target existing preset
        target = ROOT / 'data/presets/agency.json'
        original_bytes = target.read_bytes()
        original_hash = hashlib.sha256(original_bytes).hexdigest()

        with tempfile.TemporaryDirectory() as tmp:
            # 1. Valid plan preview with colliding slug
            valid_plan_file = Path(tmp) / 'valid_plan.json'
            valid_plan_file.write_text(json.dumps({
                "name": "Agency Collision Test",
                "pages": [{"name": "Home", "sections": [{"kind": "hero", "title": "Hero", "body": "Body"}]}]
            }))
            res = subprocess.run([
                sys.executable, str(ROOT / 'scripts/from_plan.py'),
                str(valid_plan_file), '--name', 'agency'
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Expected 0, got {res.returncode}: {res.stderr}")
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), original_hash,
                             "Existing preset must not be modified or deleted during valid plan preview")

            # 2. Invalid plan preview with colliding slug
            invalid_plan_file = Path(tmp) / 'invalid_plan.json'
            # Tone or page structure invalid
            invalid_plan_file.write_text(json.dumps({
                "name": "Invalid Plan",
                "tone": "nonexistent_tone_123",
                "pages": []
            }))
            res_invalid = subprocess.run([
                sys.executable, str(ROOT / 'scripts/from_plan.py'),
                str(invalid_plan_file), '--name', 'agency'
            ], capture_output=True, text=True)
            self.assertEqual(res_invalid.returncode, 1, "Expected validation failure code 1")
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), original_hash,
                             "Existing preset must not be modified or deleted during invalid plan preview")

    def test_planner_section_names_are_compiled_not_dropped(self):
        # A real planner export names sections by their planner labels, not module keys.
        plan = {"version": 1, "projects": [{"name": "Oak Plumbing", "pages": [
            {"name": "Home", "purpose": "Win calls", "sections": [
                {"kind": "Introduction", "title": "Fast local plumbing", "body": "We fix leaks."},
                {"kind": "Services", "title": "What we do", "body": "Drains - Unblocking\nBoilers - Repair"},
                {"kind": "FAQ", "title": "Questions", "body": "Weekends: Yes, by appointment."}]},
            {"name": "Contact", "sections": [{"kind": "Contact", "title": "Reach us", "body": "Call us"}]}]}]}
        slug, preset = convert_plan_to_preset(plan, self.registry)
        self.assertEqual([s["module"] for s in preset["pages"]["home"]["sections"]], ["hero", "services", "faq"])
        self.assertEqual([s["module"] for s in preset["pages"]["contact"]["sections"]], ["hero", "contact"])
        self.assertEqual(preset["sections"]["home-hero-1"]["title"], "Fast local plumbing")
        services = preset["sections"]["home-services-2"]["items"]
        self.assertEqual([i["title"] for i in services], ["Drains", "Boilers"])
        self.assertEqual(validate(ROOT, extra_presets={slug: preset}), [])

    def test_planner_labels_match_workflow(self):
        import re
        source = (ROOT / 'assets/js/workflow.js').read_text()
        found = re.search(r'const legacy=\{([^}]*)\}', source)
        self.assertIsNotNone(found, 'workflow.js legacy label map not found')
        labels = dict(re.findall(r"(\w+):'([^']*)'", found.group(1)))
        self.assertEqual(labels, PLANNER_LABELS)

    def test_unknown_section_type_is_an_error(self):
        plan = {"name": "X", "pages": [{"name": "Home", "sections": [{"kind": "Carousel"}]}]}
        with self.assertRaisesRegex(ValueError, 'Carousel'):
            convert_plan_to_preset(plan, self.registry)

    def test_duplicate_page_addresses_are_an_error(self):
        plan = {"name": "X", "pages": [{"name": "About", "sections": []}, {"name": "About!", "sections": []}]}
        with self.assertRaisesRegex(ValueError, '/about/'):
            convert_plan_to_preset(plan, self.registry)

    def test_list_markers_are_stripped_but_leading_digits_kept(self):
        items = parse_items('- 24/7 emergency - Always on call\n2. 2024 Award: Best builder\n3) Third: Item')
        self.assertEqual([i['title'] for i in items], ['24/7 emergency', '2024 Award', 'Third'])

    def test_missing_facts_are_marked_not_invented(self):
        plan = {"name": "Bare", "pages": [{"name": "Home", "sections": [{"kind": "hero"}]}]}
        _, preset = convert_plan_to_preset(plan, self.registry)
        text = json.dumps(preset)
        for invented in ('$100', 'Every Monday', 'Main Studio', 'Monday to Friday', 'Consulting'):
            self.assertNotIn(invented, text)
        self.assertIn(TBC, text)

    def test_scope_groups_are_kept_or_required_never_guessed(self):
        page = lambda items: {"name": "X", "pages": [{"name": "Home", "sections": [
            {"kind": "hero"}, {"kind": "inclusions", "title": "Scope", "body": "Design - Pages", **items}]}]}
        with self.assertRaisesRegex(ValueError, 'included, excluded'):
            convert_plan_to_preset(page({}), self.registry)
        slug, preset = convert_plan_to_preset(page({"items": [
            {"title": "Design", "text": "Pages", "group": "included"},
            {"title": "Hosting", "text": "Client account", "group": "excluded"}]}), self.registry)
        key = preset["pages"]["home"]["sections"][1]["content"]
        self.assertEqual([i["group"] for i in preset["sections"][key]["items"]], ["included", "excluded"])
        self.assertEqual(validate(ROOT, extra_presets={slug: preset}), [])

    def test_write_refuses_to_replace_an_existing_preset(self):
        import hashlib
        import subprocess
        target = ROOT / 'data/presets/agency.json'
        original = hashlib.sha256(target.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / 'plan.json'
            plan.write_text(json.dumps({"name": "Agency", "pages": [{"name": "Home", "sections": [{"kind": "hero"}]}]}))
            res = subprocess.run([sys.executable, str(ROOT / 'scripts/from_plan.py'), str(plan), '--write'],
                                 capture_output=True, text=True)
        self.assertEqual(res.returncode, 2, res.stderr)
        self.assertIn('already exists', res.stderr)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), original)

    def test_planned_destination_is_not_replaced(self):
        # A section that names where its action goes keeps that destination. Sending every visitor
        # to /contact/ regardless is a silent change of the plan.
        plan = {"name": "Destinations", "pages": [
            {"name": "Home", "slug": "home", "sections": [
                {"kind": "hero", "title": "Welcome", "body": "Intro copy.", "cta": "See services", "target": "/services/"}]},
            {"name": "Services", "slug": "services", "sections": [
                {"kind": "services", "title": "Services", "body": "One\nTwo"}]},
        ]}
        _, preset = convert_plan_to_preset(plan, self.registry)
        self.assertEqual(preset['sections']['home-hero-1']['action']['url'], '/services/')

    def test_destination_without_a_page_is_refused(self):
        plan = {"name": "Dangling", "pages": [{"name": "Home", "slug": "home", "sections": [
            {"kind": "hero", "title": "Welcome", "body": "Intro.", "cta": "Book", "target": "/booking/"}]}]}
        with self.assertRaises(ValueError) as caught:
            convert_plan_to_preset(plan, self.registry)
        self.assertIn('/booking/', str(caught.exception))

    def test_carried_page_key_survives_a_renamed_title(self):
        # "Sample work" used to compile to /sample-work/, breaking every link to /work/.
        plan = {"name": "Keys", "pages": [
            {"name": "Home", "slug": "home", "sections": [{"kind": "hero", "title": "Home", "body": "Intro."}]},
            {"name": "Sample work", "slug": "work", "sections": [{"kind": "work", "title": "Work", "body": "One\nTwo"}]},
        ]}
        _, preset = convert_plan_to_preset(plan, self.registry)
        self.assertIn('work', preset['pages'])
        self.assertNotIn('sample-work', preset['pages'])
        self.assertEqual(preset['pages']['work']['title'], 'Sample work')

    def test_page_order_follows_the_plan(self):
        plan = {"name": "Order", "pages": [
            {"name": "Home", "slug": "home", "sections": [{"kind": "hero", "title": "Home", "body": "Intro."}]},
            {"name": "Zebra", "slug": "zebra", "sections": [{"kind": "about", "title": "Zebra", "body": "Copy."}]},
            {"name": "Apple", "slug": "apple", "sections": [{"kind": "about", "title": "Apple", "body": "Copy."}]},
        ]}
        _, preset = convert_plan_to_preset(plan, self.registry)
        planned = [k for k in preset['pages'] if k in ('home', 'zebra', 'apple')]
        self.assertEqual(planned, ['home', 'zebra', 'apple'])

    def test_section_anchor_is_kept(self):
        plan = {"name": "Anchors", "pages": [{"name": "Home", "slug": "home", "sections": [
            {"kind": "hero", "title": "Home", "body": "Intro.", "anchor": "top"}]}]}
        _, preset = convert_plan_to_preset(plan, self.registry)
        self.assertEqual(preset['pages']['home']['sections'][0]['anchor'], 'top')

    def test_dropped_items_are_refused_not_truncated(self):
        body = '\n'.join(f'Item {n}: detail {n}' for n in range(1, 12))
        plan = {"name": "Long", "pages": [{"name": "Home", "slug": "home", "sections": [
            {"kind": "hero", "title": "Home", "body": "Intro."},
            {"kind": "services", "title": "Services", "body": body}]}]}
        with self.assertRaises(ValueError) as caught:
            convert_plan_to_preset(plan, self.registry)
        self.assertIn('11 lines', str(caught.exception))

    def test_structured_items_carry_their_classification(self):
        plan = {"name": "Groups", "pages": [{"name": "Home", "slug": "home", "sections": [
            {"kind": "hero", "title": "Home", "body": "Intro."},
            {"kind": "fit", "title": "Fit", "body": "ignored", "items": [
                {"title": "Groundworks", "text": "Yes", "group": "fit"},
                {"title": "Interior design", "text": "No", "group": "alternative"}]}]}]}
        _, preset = convert_plan_to_preset(plan, self.registry)
        self.assertEqual([i['group'] for i in preset['sections']['home-fit-2']['items']], ['fit', 'alternative'])

    def test_legacy_backups_without_page_keys_still_compile(self):
        # Exports written before the planner carried page keys, structured items, anchors, and the
        # brief builder's service list. They record which starter they came from, so those are
        # recovered from it rather than guessed, and the original routes survive.
        legacy = json.loads((ROOT / 'reports/review-2026-09-25/starter-exports.json').read_text())
        for entry in legacy:
            with self.subTest(starter=entry['slug']):
                project = entry['project']
                self.assertTrue(all(page.get('slug') is None for page in project['pages']),
                                'fixture must predate carried page keys')
                _, preset = convert_plan_to_preset(project, self.registry)
                original = json.loads((ROOT / 'data/presets' / f"{entry['slug']}.json").read_text())
                for key in original['pages']:
                    self.assertIn(key, preset['pages'], f"{entry['slug']}: route /{key}/ was renamed")

    def test_legacy_construction_keeps_its_brief_and_classifications(self):
        legacy = [e for e in json.loads((ROOT / 'reports/review-2026-09-25/starter-exports.json').read_text())
                  if e['slug'] == 'construction'][0]
        _, preset = convert_plan_to_preset(legacy['project'], self.registry)
        brief = next(s for key, s in preset['sections'].items() if 'services' in s and key.startswith('estimate-'))
        self.assertEqual(brief['services'],
                         json.loads((ROOT / 'data/presets/construction.json').read_text())['sections']['brief']['services'])
        fit = next(s for s in preset['sections'].values()
                   if isinstance(s.get('items'), list) and any(i.get('group') for i in s['items']))
        self.assertEqual([i['group'] for i in fit['items']], ['fit', 'fit', 'alternative'])
        anchors = [spec.get('anchor') for spec in preset['pages']['estimate']['sections']]
        self.assertIn('project-brief', anchors, 'the anchor /estimate/#project-brief points at must survive')

if __name__ == '__main__':
    unittest.main()
