#!/usr/bin/env python3
"""The doctor accepts only the pinned Hugo Extended build."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doctor  # noqa: E402

class DoctorTests(unittest.TestCase):
    def test_hugo_must_be_extended_and_pinned(self):
        self.assertTrue(doctor.hugo_ok('hugo v0.166.0+extended+withdeploy darwin/arm64 BuildDate=x', '0.166.0'))
        self.assertFalse(doctor.hugo_ok('hugo v0.166.0 darwin/arm64', '0.166.0'), 'the standard build cannot compile the styles')
        self.assertFalse(doctor.hugo_ok('hugo v0.165.0+extended darwin/arm64', '0.166.0'))
        self.assertFalse(doctor.hugo_ok('', '0.166.0'), 'a missing hugo is not ok')

    def test_a_check_reports_a_fix_only_when_it_fails(self):
        for check in (doctor.check_python, doctor.check_git):
            status, label, fix = check()
            self.assertIn(status, ('ok', 'FIX'))
            self.assertEqual(bool(fix), status != 'ok', label)

if __name__ == '__main__':
    unittest.main()
