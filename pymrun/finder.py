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


def _should_skip(path: Path) -> bool:
    for part in path.parts:
        if part.startswith(".") and part != ".":
            return True
        if part in SKIP_DIRS:
            return True
    return False


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
    for pyfile in root.rglob("*.py"):
        if _should_skip(pyfile):
            continue
        qname = to_module_format(root, pyfile)
        basename = pyfile.stem
        index.setdefault(basename, []).append(qname)

    for v in index.values():
        v.sort()

    return index
