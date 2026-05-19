from __future__ import annotations

from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from pymrun.cli import _complete_basename, _detect_shell, _install_completion, main


class TestCompleteBasename:
    def test_returns_matching_items(
        self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_project)
        ctx = click.Context(main)
        param = click.Argument(["module_name"])
        result = _complete_basename(ctx, param, "mai")
        names = [item.value for item in result]
        assert "main" in names
        assert "utils" not in names

    def test_returns_empty_on_no_match(
        self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_project)
        ctx = click.Context(main)
        param = click.Argument(["module_name"])
        result = _complete_basename(ctx, param, "zzz")
        assert result == []

    def test_returns_all_when_empty_prefix(
        self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_project)
        ctx = click.Context(main)
        param = click.Argument(["module_name"])
        result = _complete_basename(ctx, param, "")
        names = {item.value for item in result}
        assert "main" in names
        assert "utils" in names
        assert "helper" in names


class TestDetectShell:
    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("/bin/bash", "bash"),
            ("/usr/bin/bash", "bash"),
            ("/usr/local/bin/zsh", "zsh"),
            ("/bin/zsh", "zsh"),
            ("/usr/bin/fish", "fish"),
            ("/usr/local/bin/fish", "fish"),
        ],
    )
    def test_from_shell_env(
        self, env_value: str, expected: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SHELL", env_value)
        monkeypatch.delenv("PSModulePath", raising=False)
        assert _detect_shell() == expected

    def test_powershell(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SHELL", raising=False)
        monkeypatch.setenv("PSModulePath", "C:\\Users\\me\\Documents\\PowerShell")
        assert _detect_shell() == "powershell"

    def test_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SHELL", raising=False)
        monkeypatch.delenv("PSModulePath", raising=False)
        assert _detect_shell() is None


class TestMainCLI:
    def test_no_args_shows_help(self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_project)
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Run a Python module via uv by its basename" in result.output
        assert "MODULE_NAME" in result.output

    def test_module_not_found(self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_project)
        runner = CliRunner()
        result = runner.invoke(main, ["nonexistent"])
        assert result.exit_code != 0
        assert "No module named 'nonexistent' found" in result.output

    def test_runs_unique_module(self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_project)
        calls: list[tuple[str, list[str]]] = []

        def fake_run_module(module: str, extra: list[str]) -> None:
            calls.append((module, extra))

        monkeypatch.setattr("pymrun.cli.run_module", fake_run_module)
        runner = CliRunner()
        result = runner.invoke(main, ["utils"])
        # run_module is mocked so execution falls through to sys.exit(1)
        assert result.exit_code == 1
        assert len(calls) == 1
        assert calls[0] == ("src.app.utils", [])

    def test_prompts_on_duplicate(self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_project)
        calls: list[tuple[str, list[str]]] = []

        def fake_run_module(module: str, extra: list[str]) -> None:
            calls.append((module, extra))

        monkeypatch.setattr("pymrun.cli.run_module", fake_run_module)
        runner = CliRunner()
        # Select option 2 (subpkg.main)
        result = runner.invoke(main, ["main"], input="2\n")
        assert result.exit_code == 1
        assert "Multiple modules named 'main' found:" in result.output
        assert len(calls) == 1
        assert calls[0] == ("src.app.subpkg.main", [])

    def test_prompts_default_choice(
        self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_project)
        calls: list[tuple[str, list[str]]] = []

        def fake_run_module(module: str, extra: list[str]) -> None:
            calls.append((module, extra))

        monkeypatch.setattr("pymrun.cli.run_module", fake_run_module)
        runner = CliRunner()
        # Press enter to accept default (option 1)
        result = runner.invoke(main, ["main"], input="\n")
        assert result.exit_code == 1
        assert len(calls) == 1
        assert calls[0] == ("src.app.main", [])

    def test_forwards_extra_args(self, tmp_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_project)
        calls: list[tuple[str, list[str]]] = []

        def fake_run_module(module: str, extra: list[str]) -> None:
            calls.append((module, extra))

        monkeypatch.setattr("pymrun.cli.run_module", fake_run_module)
        runner = CliRunner()
        result = runner.invoke(main, ["helper", "--", "--flag", "value"])
        assert result.exit_code == 1
        assert len(calls) == 1
        assert calls[0] == ("src.lib.helper", ["--flag", "value"])


class TestInstallCompletion:
    def test_bash_script_written(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Ensure rc file exists
        bashrc = fake_home / ".bashrc"
        bashrc.write_text("# existing\n")

        runner = CliRunner()
        result = runner.invoke(main, ["--install-completion", "--shell=bash"])
        assert result.exit_code == 0

        script_path = fake_home / ".config" / "pymrun" / "pymrun.bash"
        assert script_path.exists()
        content = script_path.read_text()
        assert "_pymrun_completion" in content or "PYMRUN_COMPLETE" in content

        rc_content = bashrc.read_text()
        assert 'source "' + str(script_path) + '"' in rc_content

    def test_zsh_script_written(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        zshrc = fake_home / ".zshrc"
        zshrc.write_text("# existing\n")

        runner = CliRunner()
        result = runner.invoke(main, ["--install-completion", "--shell=zsh"])
        assert result.exit_code == 0

        script_path = fake_home / ".config" / "pymrun" / "pymrun.zsh"
        assert script_path.exists()

        rc_content = zshrc.read_text()
        assert 'source "' + str(script_path) + '"' in rc_content

    def test_fish_script_written(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        fish_config = fake_home / ".config" / "fish" / "config.fish"
        fish_config.parent.mkdir(parents=True)
        fish_config.write_text("# existing\n")

        runner = CliRunner()
        result = runner.invoke(main, ["--install-completion", "--shell=fish"])
        assert result.exit_code == 0

        script_path = fake_home / ".config" / "pymrun" / "pymrun.fish"
        assert script_path.exists()

        rc_content = fish_config.read_text()
        assert 'source "' + str(script_path) + '"' in rc_content

    def test_skips_duplicate_rc_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        bashrc = fake_home / ".bashrc"
        bashrc.write_text("# existing\n")

        runner = CliRunner()
        # First install
        result1 = runner.invoke(main, ["--install-completion", "--shell=bash"])
        assert result1.exit_code == 0
        assert "Added source line to:" in result1.output

        # Second install should report already present
        result2 = runner.invoke(main, ["--install-completion", "--shell=bash"])
        assert result2.exit_code == 0
        assert "Source line already present in:" in result2.output

        # Verify only one source line exists
        rc_lines = [line for line in bashrc.read_text().splitlines() if "pymrun" in line.lower()]
        assert len(rc_lines) == 2  # comment + source line

    def test_unsupported_shell_raises(self) -> None:
        # This is hard to trigger through the CLI because --shell is validated by Choice,
        # but we can test _install_completion directly with a fake name.
        with pytest.raises(click.ClickException, match="does not support completion"):
            _install_completion("unknown_shell")
