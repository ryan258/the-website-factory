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

if __name__ == '__main__':
    unittest.main()
