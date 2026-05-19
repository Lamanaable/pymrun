from __future__ import annotations

import os
import sys
from pathlib import Path

import click
from click.shell_completion import CompletionItem

from pymrun.finder import discover_module_basenames, discover_modules, find_project_root
from pymrun.runner import run_module


def _complete_basename(
    ctx: click.Context,
    param: click.Argument,
    incomplete: str,
) -> list[CompletionItem]:
    root = find_project_root()
    basenames = discover_module_basenames(root)
    return [CompletionItem(name) for name in basenames if name.startswith(incomplete)]


def _detect_shell() -> str | None:
    shell = os.environ.get("SHELL", "")
    if "bash" in shell:
        return "bash"
    if "zsh" in shell:
        return "zsh"
    if "fish" in shell:
        return "fish"
    if os.environ.get("PSModulePath"):
        return "powershell"
    return None


def _install_completion(shell: str) -> None:
    import contextlib
    import io

    from click.shell_completion import get_completion_class

    complete_var = "_PYMRUN_COMPLETE"

    prog_name = "pymrun"

    comp_cls = get_completion_class(shell)
    if comp_cls is None:
        raise click.ClickException(f"Click does not support completion for: {shell}")

    if shell == "bash":
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            completion = comp_cls(
                cli=main,  # type: ignore[arg-type]
                ctx_args={},
                prog_name=prog_name,
                complete_var=complete_var,
            ).source()
        # Remove -o nosort so the script works on macOS default bash 3.2
        completion = completion.replace("complete -o nosort -F", "complete -F")
    else:
        completion = comp_cls(
            cli=main,  # type: ignore[arg-type]
            ctx_args={},
            prog_name=prog_name,
            complete_var=complete_var,
        ).source()

    config_dir = Path.home() / ".config" / "pymrun"
    config_dir.mkdir(parents=True, exist_ok=True)
    script_path = config_dir / f"pymrun.{shell}"
    script_path.write_text(completion)

    click.echo(f"Completion script saved to: {script_path}")

    if shell in ("bash", "zsh", "fish"):
        rc_file = _rc_file_for_shell(shell)
        source_line = f'source "{script_path}"'
        if rc_file and rc_file.exists():
            contents = rc_file.read_text()
            if source_line not in contents:
                with rc_file.open("a") as fh:
                    fh.write(f"\n# pymrun shell completion\n{source_line}\n")
                click.echo(f"Added source line to: {rc_file}")
            else:
                click.echo(f"Source line already present in: {rc_file}")
        else:
            click.echo(f"Could not find {rc_file}; add this line manually:")
            click.echo(f"  {source_line}")
    elif shell == "powershell":
        click.echo("Add the following line to your PowerShell profile ($PROFILE):")
        click.echo(f'  . "{script_path}"')
        click.echo("Or run this command to append it:")
        click.echo(f"  Add-Content -Path $PROFILE -Value '. \"{script_path}\"'")


def _rc_file_for_shell(shell: str) -> Path | None:
    home = Path.home()
    if shell == "bash":
        for name in (".bashrc", ".bash_profile", ".profile"):
            p = home / name
            if p.exists():
                return p
        return home / ".bashrc"
    if shell == "zsh":
        return home / ".zshrc"
    if shell == "fish":
        return home / ".config" / "fish" / "config.fish"
    return None


@click.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
@click.argument("module_name", required=False, shell_complete=_complete_basename)
@click.option(
    "--install-completion",
    is_flag=True,
    help="Install shell completion script and update your shell rc file.",
)
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Explicitly specify shell for --install-completion.",
)
@click.pass_context
def main(
    ctx: click.Context,
    module_name: str | None,
    install_completion: bool,
    shell: str | None,
) -> None:
    """Run a Python module via uv by its basename.

    MODULE_NAME is the stem of the Python file you want to run (e.g. ``helper``
    for ``src/utils/helper.py``).  All remaining arguments are forwarded to the
    target module.

    Examples:
      pymrun myscript
      pymrun myscript -- --flag value
    """
    if install_completion:
        detected = shell or _detect_shell()
        if detected is None:
            raise click.ClickException("Could not detect shell. Please specify with --shell.")
        _install_completion(detected)
        ctx.exit(0)

    if module_name is None:
        click.echo(ctx.get_help())
        ctx.exit(0)

    root = find_project_root()
    index = discover_modules(root)
    matches: list[str] = index.get(module_name, []) or []

    if not matches:
        click.echo(f"No module named '{module_name}' found under {root}.", err=True)
        raise click.Abort()

    chosen = _select_module(matches, module_name)

    extra: list[str] = ctx.args
    run_module(chosen, extra)
    sys.exit(1)  # pragma: no cover


def _select_module(matches: list[str], module_name: str) -> str:
    if len(matches) == 1:
        return matches[0]

    click.echo(f"Multiple modules named '{module_name}' found:")
    for i, m in enumerate(matches, 1):
        click.echo(f"  {i}. {m}")
    choice: int = click.prompt(
        "Select module",
        type=click.IntRange(1, len(matches)),
        default=1,
    )
    return matches[choice - 1]
