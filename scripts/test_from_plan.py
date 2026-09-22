#!/usr/bin/env python3
"""Tests for scripts/from_plan.py planner-to-preset converter."""
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
from from_plan import convert_plan_to_preset
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
        
        # Test validation against factory rules
        target = ROOT / 'data/presets' / f"{slug}.json"
        try:
            target.write_text(json.dumps(preset, indent=2) + '\n')
            errors = validate(ROOT)
            self.assertEqual(errors, [], f"Validation failed with: {errors}")
        finally:
            target.unlink(missing_ok=True)

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
        
        target = ROOT / 'data/presets' / f"{slug}.json"
        try:
            target.write_text(json.dumps(preset, indent=2) + '\n')
            errors = validate(ROOT)
            self.assertEqual(errors, [], f"Validation failed with: {errors}")
        finally:
            target.unlink(missing_ok=True)

if __name__ == '__main__':
    unittest.main()
