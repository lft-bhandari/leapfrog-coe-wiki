from __future__ import annotations

import json

import pytest

from core.metadata import DocMetadata, extract_metadata

_FULL_HEADER = """\
Document Title
Context Engineering
Prepared by
AI COE: Samir Dahal
Reviewed By
Muskan Bhandari Kalash Shrestha
Documented Date
28th May, 2026
Last Updated Date
28th May, 2026
Status
Under review
Review Cycle
Q2 2026
"""

_NO_HEADER = """\
# My Local Doc

Just some content with no CoE metadata header.
"""


def _make_chat_fn(response: str):
    """Return a mock ChatFn that always returns the given string."""
    def _fn(system: str, user: str) -> str:
        return response
    return _fn


def test_extract_metadata_returns_docmetadata():
    payload = json.dumps({
        'author': ['Samir Dahal'],
        'reviewed_by': ['Muskan Bhandari', 'Kalash Shrestha'],
        'documented_date': '28th May, 2026',
        'last_updated_date': '28th May, 2026',
        'review_cycle': 'Q2 2026',
    })
    chat_fn = _make_chat_fn(payload)

    meta = extract_metadata(_FULL_HEADER, chat_fn)

    assert isinstance(meta, DocMetadata)
    assert meta.author == ['Samir Dahal']
    assert meta.reviewed_by == ['Muskan Bhandari', 'Kalash Shrestha']
    assert meta.documented_date == '28th May, 2026'
    assert meta.review_cycle == 'Q2 2026'


def test_extract_metadata_defaults_missing_fields():
    payload = json.dumps({'author': ['Someone']})
    chat_fn = _make_chat_fn(payload)

    meta = extract_metadata(_FULL_HEADER, chat_fn)

    assert meta.reviewed_by == ['Unknown']
    assert meta.documented_date == 'Unknown'
    assert meta.last_updated_date == 'Unknown'
    assert meta.review_cycle == 'Unknown'


def test_extract_metadata_handles_malformed_llm_response():
    chat_fn = _make_chat_fn('not valid json at all')

    meta = extract_metadata(_FULL_HEADER, chat_fn)

    assert meta.author == ['Unknown']
    assert meta.reviewed_by == ['Unknown']


def test_extract_metadata_handles_llm_json_in_markdown_fence():
    payload = '```json\n' + json.dumps({'author': ['Alice']}) + '\n```'
    chat_fn = _make_chat_fn(payload)

    meta = extract_metadata(_FULL_HEADER, chat_fn)

    assert meta.author == ['Alice']


def test_extract_metadata_all_unknown_emits_warn_for_drive_doc(capsys):
    chat_fn = _make_chat_fn('{}')

    extract_metadata(_FULL_HEADER, chat_fn, is_drive_doc=True)

    assert '[warn]' in capsys.readouterr().err


def test_extract_metadata_all_unknown_no_warn_for_local_doc(capsys):
    chat_fn = _make_chat_fn('{}')

    extract_metadata(_NO_HEADER, chat_fn, is_drive_doc=False)

    assert capsys.readouterr().err == ''


def test_extract_metadata_only_sends_top_of_doc():
    """LLM receives at most the first ~3000 chars, not the full document."""
    seen: list[str] = []

    def _capturing_fn(system: str, user: str) -> str:
        seen.append(user)
        return '{}'

    long_doc = _FULL_HEADER + ('x' * 10_000)
    extract_metadata(long_doc, _capturing_fn)

    assert len(seen[0]) < 4_000
