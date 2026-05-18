from pathlib import Path

import pytest

from pymrun.finder import (
    _should_skip,
    discover_modules,
    find_project_root,
    to_module_format,
)


class TestFindProjectRoot:
    def test_with_pyproject_toml(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        (root / "pyproject.toml").write_text("[project]\n")
        sub = root / "src" / "app"
        sub.mkdir(parents=True)
        assert find_project_root(sub) == root

    def test_with_requirements_txt(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        (root / "requirements.txt").write_text("click\n")
        sub = root / "src"
        sub.mkdir()
        assert find_project_root(sub) == root

    def test_no_marker_returns_start(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert find_project_root(empty) == empty

    def test_none_uses_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        assert find_project_root(None) == tmp_path


class TestShouldSkip:
    @pytest.mark.parametrize(
        "path,expected",
        [
            (Path("src/main.py"), False),
            (Path(".hidden/secret.py"), True),
            (Path("venv/fake.py"), True),
            (Path("__pycache__/cached.py"), True),
            (Path("dist/setup.py"), True),
            (Path("build/compile.py"), True),
            (Path("node_modules/index.py"), True),
            (Path(".git/hooks/pre-commit.py"), True),
            (Path("repo/src/main.py"), False),
            (Path("repo/.secret/stuff.py"), True),
        ],
    )
    def test_should_skip(self, path: Path, expected: bool) -> None:
        assert _should_skip(path) is expected


class TestToModuleFormat:
    @pytest.mark.parametrize(
        "root,pyfile,expected",
        [
            (Path("/project"), Path("/project/src/app/main.py"), "src.app.main"),
            (Path("/project"), Path("/project/plain.py"), "plain"),
            (Path("/project"), Path("/project/tests/test_app.py"), "tests.test_app"),
            (Path("/a/b"), Path("/a/b/c.py"), "c"),
        ],
    )
    def test_to_module_format(self, root: Path, pyfile: Path, expected: str) -> None:
        assert to_module_format(root, pyfile) == expected


class TestDiscoverModules:
    def test_indexes_basenames(self, tmp_project: Path) -> None:
        index = discover_modules(tmp_project)
        assert index["main"] == ["src.app.main", "src.app.subpkg.main"]
        assert index["utils"] == ["src.app.utils"]
        assert index["helper"] == ["src.lib.helper"]
        assert index["plain"] == ["plain"]
        assert index["test_app"] == ["tests.test_app"]
        assert index["conftest"] == ["tests.conftest"]

    def test_collects_duplicates(self, tmp_project: Path) -> None:
        index = discover_modules(tmp_project)
        assert len(index["main"]) == 2

    def test_sorts_lists(self, tmp_project: Path) -> None:
        index = discover_modules(tmp_project)
        for names in index.values():
            assert names == sorted(names)

    def test_skips_ignored_dirs(self, tmp_project: Path) -> None:
        index = discover_modules(tmp_project)
        assert "fake" not in index  # venv/
        assert "cached" not in index  # __pycache__/
        assert "secret" not in index  # .hidden/
        assert "setup" not in index  # dist/
        assert "compile" not in index  # build/
        assert "index" not in index  # node_modules/

    def test_empty_project(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        index = discover_modules(empty)
        assert index == {}
