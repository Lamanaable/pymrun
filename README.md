# pymrun

Fuzzy Python module runner for `uv`.

## What it does

`pymrun` indexes all `.py` files under your project root (detected by `pyproject.toml` or `requirements.txt`) and lets you run them as modules by **basename** instead of typing out the full dotted path.

## Usage

```bash
# Run src/utils/helper.py
pymrun helper

# Run with extra arguments forwarded to the module
pymrun helper -- --flag value

# If there are multiple files with the same basename, a prompt lets you pick
```

## Shell Completion

### Bash / Zsh / Fish

Run once to install:

```bash
pymrun --install-completion
```

If your shell cannot be auto-detected, specify it explicitly:

```bash
pymrun --install-completion --shell=zsh
```

Then restart your terminal (or `source` your rc file).

### PowerShell

Run:

```powershell
pymrun --install-completion
```

Then add the printed line to your PowerShell profile (`$PROFILE`):

```powershell
. "$HOME\.config\pymrun\pymrun.ps1"
```

### Manual setup (any shell)

You can also source the generated completion script directly:

```bash
# Bash example
eval "$(_PYMRUN_COMPLETE=bash_source pymrun)"
```

## How it works

1. **Root detection** — walks up from `cwd` looking for `pyproject.toml` or `requirements.txt`.
2. **Indexing** — recursively scans the project for `.py` files, skipping caches, venvs, and hidden dirs.
3. **Execution** — converts the chosen file to a fully-qualified module name and runs `uv run -m <module>` via `os.execvp` so signals flow directly to `uv`.

## Requirements

- Python ≥ 3.14
- `uv` installed and on your `$PATH`
