import json
from pathlib import Path
import tempfile
import unittest

from scaffold_core import copy_sources


class SourceCopyTests(unittest.TestCase):
    def test_allowlist_portability_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; source.mkdir()
            (source / "scripts").mkdir(); (source / "scripts/tool.py").write_text("pass\n")
            (source / "scripts/.env").write_text("private")
            (source / "README.md").write_text("Example")
            target = copy_sources(source, root / "client", ("scripts",), ("README.md",))
            self.assertFalse((target / "scripts/.env").exists())
            self.assertTrue((target / "scripts/scaffold_core.py").is_file())
            self.assertFalse(json.loads((target / "scripts/scaffold-origin.json").read_text())["approval_inherited"])
            with self.assertRaises(FileExistsError):
                copy_sources(source, target, ("scripts",), ("README.md",))
            self.assertEqual((target / "README.md").read_text(), "Example")

    def test_symlink_and_traversal_refused_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; source.mkdir()
            (source / "scripts").mkdir(); (source / "scripts/link").symlink_to(root)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                copy_sources(source, root / "client", ("scripts",), ())
            self.assertFalse((root / "client").exists())
            with self.assertRaises(ValueError):
                copy_sources(source, root / "client", (), ("../private",))


if __name__ == "__main__":
    unittest.main()
