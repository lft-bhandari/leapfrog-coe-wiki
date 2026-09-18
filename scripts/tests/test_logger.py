from __future__ import annotations

import sys
from io import StringIO

import pytest

from core.logger import error, info, warn


def test_info_writes_to_stdout(capsys):
    info('[ingest] processing doc')

    captured = capsys.readouterr()
    assert '[ingest] processing doc' in captured.out
    assert captured.err == ''


def test_warn_writes_to_stderr_with_prefix(capsys):
    warn('no metadata header found')

    captured = capsys.readouterr()
    assert captured.out == ''
    assert '[warn] no metadata header found' in captured.err


def test_error_writes_to_stderr_with_prefix(capsys):
    error('synthesis failed')

    captured = capsys.readouterr()
    assert captured.out == ''
    assert '[error] synthesis failed' in captured.err


def test_warn_does_not_add_double_prefix(capsys):
    warn('already tagged message')

    captured = capsys.readouterr()
    assert captured.err.count('[warn]') == 1
