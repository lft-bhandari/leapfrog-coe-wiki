from __future__ import annotations

import sys


def info(msg: str) -> None:
    """Write a log line to stdout.

    Callers are responsible for embedding their own context tag (e.g. '[ingest] ...'),
    unlike warn/error which add their prefix automatically.
    """
    print(msg)


def warn(msg: str) -> None:
    """Write a [warn]-prefixed message to stderr."""
    print(f'[warn] {msg}', file=sys.stderr)


def error(msg: str) -> None:
    """Write an [error]-prefixed message to stderr."""
    print(f'[error] {msg}', file=sys.stderr)
