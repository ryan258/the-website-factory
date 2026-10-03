"""Shared source-copy contract for the factory and its vertical masters.

Client copies carry this exact module, so they remain independent of the factory.
Brand/content neutralization remains the responsibility of each vertical adapter.
"""
import hashlib
import json
from pathlib import Path
import shutil

VERSION = 1
EXCLUDED = {".git", ".env", ".DS_Store", "__pycache__", "node_modules", ".venv", "public", "resources"}


def _ignored(_directory, names):
    return {name for name in names if name in EXCLUDED or name.startswith(".env.") or name.endswith(".pyc")}


def copy_sources(source, destination, folders, files):
    """Copy an explicit source allowlist into a new directory; never overwrite.

    Reject symlinks before writing. Roll back only a directory this call created
    if copying fails. Emit a source receipt and the portable shared implementation.
    """
    source = Path(source).resolve()
    destination = Path(destination).expanduser().absolute()
    resolved = destination.resolve()
    if resolved == source or source in resolved.parents:
        raise ValueError("Choose a destination outside the source project.")
    names = tuple(folders) + tuple(files)
    if len(names) != len(set(names)):
        raise ValueError("Duplicate scaffold source entry")
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or _ignored("", relative.parts):
            raise ValueError(f"Invalid scaffold source entry: {name}")
        path = source / name
        if not path.exists() or path.is_symlink():
            raise ValueError(f"Missing or symlinked scaffold source: {name}")
        if any(parent.is_symlink() for parent in path.parents if parent != source and source in parent.parents):
            raise ValueError(f"Symlinked scaffold source parent: {name}")
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_symlink():
                    raise ValueError(f"Source symlinks are not copied: {child.relative_to(source)}")
    destination.mkdir()  # Outside rollback: a pre-existing destination must survive.
    try:
        for folder in folders:
            shutil.copytree(source / folder, destination / folder, ignore=_ignored)
        for name in files:
            shutil.copy2(source / name, destination / name)
        scripts = destination / "scripts"
        scripts.mkdir(exist_ok=True)
        implementation = Path(__file__).read_bytes()
        (scripts / "scaffold_core.py").write_bytes(implementation)
        (scripts / "scaffold-origin.json").write_text(json.dumps({
            "contract_version": VERSION,
            "owner": "the-website-factory/scripts/scaffold_core.py",
            "sha256": hashlib.sha256(implementation).hexdigest(),
            "source_kind": source.name,
            "folders": list(folders), "files": list(files),
            "approval_inherited": False,
        }, indent=2) + "\n")
    except BaseException:
        shutil.rmtree(destination)
        raise
    return destination
