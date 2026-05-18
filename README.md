# pymrun

Run Python modules by basename with `uv`.

## What it does

`pymrun` indexes all `.py` files under your project root (detected by `pyproject.toml` or `requirements.txt`) and lets you run them as fully-qualified modules by **basename** instead of typing the full dotted path.

Given a project like:

```
myproject/
├── pyproject.toml
└── src/
    └── myapp/
        ├── main.py
        └── utils/
            └── helper.py
```

You can run:

```bash
pymrun helper          # instead of: uv run -m src.myapp.utils.helper
pymrun main            # instead of: uv run -m src.myapp.main
```

## Requirements

- **Python** ≥ 3.10
- **uv** installed and available on your `$PATH`

## Installation

```bash
pip install pymrun
```

Or with `uv`:

```bash
uv pip install pymrun
```

## Usage

### Run a module by basename

```bash
# Run src/myapp/utils/helper.py
pymrun helper
```

### Forward arguments to the module

Use `--` to separate `pymrun` arguments from the module's arguments:

```bash
pymrun helper -- --flag value --verbose
```

### Duplicate basenames

If multiple files share the same basename (e.g., two `main.py` files), `pymrun` lists them and prompts you to choose:

```bash
$ pymrun main
Multiple modules named 'main' found:
  1. src.myapp.main
  2. src.myapp.subpkg.main
Select module [1]:
```

### No arguments

Running `pymrun` without arguments shows the help text:

```bash
pymrun
```

## Shell Completion

### Bash / Zsh / Fish

Install completion for your current shell:

```bash
pymrun --install-completion
```

If auto-detection fails, specify the shell explicitly:

```bash
pymrun --install-completion --shell=zsh
```

Then restart your terminal or source your rc file.

### Manual setup (any shell)

You can also source the generated completion script directly:

```bash
# Bash example
eval "$(_PYMRUN_COMPLETE=bash_source pymrun)"
```

## How it works

1. **Root detection** — Walks up from the current directory looking for `pyproject.toml` or `requirements.txt`.
2. **Indexing** — Recursively scans the project for `*.py` files, skipping common build, cache, and hidden directories (`__pycache__`, `.venv`, `.git`, `dist`, `build`, `node_modules`).
3. **Execution** — Converts the chosen file to a fully-qualified module name and replaces the current process with `uv run -m <module>` via `os.execvp`, so signals (e.g., Ctrl-C) flow directly to `uv`.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/pymrun.git
cd pymrun

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install --group dev --group lint -e .
```

### Running tests

```bash
pytest
```

Or with `tox` across multiple Python versions:

```bash
tox
```

### Linting and type checking

```bash
tox -e lint
```

Or manually:

```bash
ruff check .
ruff format --check .
pyright
```

## Contributing

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automatic semantic versioning:

- `feat:` → minor version bump
- `fix:` → patch version bump
- `BREAKING CHANGE:` in commit footer → major version bump

## License

MIT
