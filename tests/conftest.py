from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a realistic temporary project layout and return its root."""
    root = tmp_path / "project"
    root.mkdir()

    # Root marker
    (root / "pyproject.toml").write_text("[project]\n")

    # Normal source files
    src = root / "src" / "app"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text("print('app main')\n")
    (src / "utils.py").write_text("print('app utils')\n")

    lib = root / "src" / "lib"
    lib.mkdir(parents=True)
    (lib / "helper.py").write_text("print('lib helper')\n")

    # Test directory
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text("")
    (tests / "conftest.py").write_text("")

    # Top-level file
    (root / "plain.py").write_text("print('plain')\n")

    # Deeper nesting for duplicate basenames
    sub = root / "src" / "app" / "subpkg"
    sub.mkdir(parents=True)
    (sub / "main.py").write_text("print('subpkg main')\n")

    # Dirs that should be skipped
    venv = root / "venv"
    venv.mkdir()
    (venv / "fake.py").write_text("")

    pycache = root / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.py").write_text("")

    hidden = root / ".hidden"
    hidden.mkdir()
    (hidden / "secret.py").write_text("")

    dist = root / "dist"
    dist.mkdir()
    (dist / "setup.py").write_text("")

    build = root / "build"
    build.mkdir()
    (build / "compile.py").write_text("")

    node_modules = root / "node_modules"
    node_modules.mkdir()
    (node_modules / "index.py").write_text("")

    return root
