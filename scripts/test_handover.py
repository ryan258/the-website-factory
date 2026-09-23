#!/usr/bin/env python3
"""scripts/handover.py reports the real state of the master and of a fresh client copy."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import handover  # noqa: E402
import new_site  # noqa: E402

class HandoverTests(unittest.TestCase):
    def test_master_report_lists_pages_settings_and_manual_checks(self):
        text, _ = handover.report()
        for expected in ('# Handover report: 258 Web Co.', '| `/privacy/` | Privacy |', 'Search engines: blocked',
                         'ENQUIRY_ENABLED` = `false`', 'Still to check by hand', 'screen-reader'):
            self.assertIn(expected, text)

    def test_copy_with_sample_content_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = new_site.create(Path(tmp) / 'client', 'Sample Co', 'consultant')
            self.assertIn('scripts/handover.py', (dest / 'docs/acceptance.md').read_text())
            result = subprocess.run([sys.executable, str(dest / 'scripts/handover.py'), '--output', 'docs/acceptance.md'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('not ready', result.stdout, 'no build yet, so output checks cannot pass')
            report = (dest / 'docs/acceptance.md').read_text()
            self.assertIn('No build output found', report)
            self.assertIn('Sample Co', report)

if __name__ == '__main__':
    unittest.main()
