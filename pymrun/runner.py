import os


def run_module(
    module: str,
    extra_args: list[str],
) -> None:
    """Replace the current process with ``uv run -m <module> [extra_args]``.

    This uses ``os.execvp`` so that signals (e.g. Ctrl-C) flow directly to
    the ``uv`` process without any intermediate wrapper.
    """
    cmd = [
        "uv",
        "run",
        "-m",
        module,
        *extra_args,
    ]

    os.execvp("uv", cmd)
