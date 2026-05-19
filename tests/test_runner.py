from __future__ import annotations

import os

import pytest

from pymrun.runner import run_module


class TestRunModule:
    def test_builds_correct_command_no_extra_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_execvp(file: str, args: list[str]) -> None:
            calls.append((file, args))

        monkeypatch.setattr(os, "execvp", fake_execvp)
        run_module("foo.bar", [])

        assert len(calls) == 1
        file, args = calls[0]
        assert file == "uv"
        assert args == ["uv", "run", "-m", "foo.bar"]

    def test_passes_extra_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_execvp(file: str, args: list[str]) -> None:
            calls.append((file, args))

        monkeypatch.setattr(os, "execvp", fake_execvp)
        run_module("myapp.main", ["--flag", "value", "--verbose"])

        assert len(calls) == 1
        file, args = calls[0]
        assert file == "uv"
        assert args == ["uv", "run", "-m", "myapp.main", "--flag", "value", "--verbose"]

    def test_single_extra_arg(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_execvp(file: str, args: list[str]) -> None:
            calls.append((file, args))

        monkeypatch.setattr(os, "execvp", fake_execvp)
        run_module("plain", ["--help"])

        assert len(calls) == 1
        file, args = calls[0]
        assert file == "uv"
        assert args == ["uv", "run", "-m", "plain", "--help"]
