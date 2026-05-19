from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

ROOT_MARKERS = ("pyproject.toml", "requirements.txt")
SKIP_DIRS = frozenset(
    {
        "__pycache__",
        "venv",
        "node_modules",
        "dist",
        "build",
    }
)


def find_project_root(start_path: Path | None = None) -> Path:
    start = start_path or Path.cwd()
    for parent in [start, *start.parents]:
        if any((parent / marker).exists() for marker in ROOT_MARKERS):
            return parent
    return start


def _should_skip_dir(name: str) -> bool:
    if name.startswith(".") and name != ".":
        return True
    if name in SKIP_DIRS:
        return True
    return False


def _should_skip_file(name: str) -> bool:
    if name.startswith(".") and name != ".":
        return True
    return False


def _scandir_walk(root: Path) -> Iterator[Path]:
    """Yield Path objects for ``*.py`` files under *root*."""
    try:
        with os.scandir(root) as it:
            for entry in it:
                name = entry.name
                if entry.is_dir(follow_symlinks=False):
                    if not _should_skip_dir(name):
                        yield from _scandir_walk(root / name)
                elif entry.is_file(follow_symlinks=False):
                    if not _should_skip_file(name) and name.endswith(".py"):
                        yield root / name
    except PermissionError:
        return


def to_module_format(
    root: Path,
    pyfile: Path,
) -> str:
    relative = pyfile.relative_to(root).with_suffix("")
    return ".".join(relative.parts)


def discover_modules(root: Path) -> dict[str, list[str]]:
    """Return a mapping of ``{basename: [qualified.module.names]}``.

    Scans *root* recursively for ``*.py`` files, skipping common build,
    cache, and hidden directories.
    """
    index: dict[str, list[str]] = {}
    for pyfile in _scandir_walk(root):
        qname = to_module_format(root, pyfile)
        basename = pyfile.stem
        index.setdefault(basename, []).append(qname)

    for v in index.values():
        v.sort()

    return index


def discover_module_basenames(root: Path) -> set[str]:
    """Return a set of all module basenames under *root*."""
    basenames: set[str] = set()
    for pyfile in _scandir_walk(root):
        basenames.add(pyfile.stem)
    return basenames
