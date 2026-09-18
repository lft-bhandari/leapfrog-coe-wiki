from __future__ import annotations

import sys


def info(msg: str) -> None:
    """Write an informational log line to stdout."""
    print(msg)


def warn(msg: str) -> None:
    """Write a warning to stderr, prefixed with [warn]."""
    print(f'[warn] {msg}', file=sys.stderr)


def error(msg: str) -> None:
    """Write an error to stderr, prefixed with [error]."""
    print(f'[error] {msg}', file=sys.stderr)
