from __future__ import annotations

import pytest

from core.preprocess import split_sections, strip_images

# ---------------------------------------------------------------------------
# strip_images
# ---------------------------------------------------------------------------

def test_strip_images_removes_markdown_image_lines():
    content = 'Some text\n![alt text](https://example.com/img.png)\nMore text\n'

    result = strip_images(content)

    assert '![' not in result
    assert 'Some text' in result
    assert 'More text' in result


def test_strip_images_removes_empty_alt_images():
    content = 'Before\n![](https://lh3.googleusercontent.com/abc123)\nAfter\n'

    result = strip_images(content)

    assert '![' not in result
    assert 'Before' in result
    assert 'After' in result


def test_strip_images_handles_multiple_images():
    content = '![a](url1)\nText\n![b](url2)\n'

    result = strip_images(content)

    assert result.strip() == 'Text'


def test_strip_images_leaves_non_image_content_unchanged():
    content = '# Heading\n\nParagraph with [a link](https://example.com).\n'

    result = strip_images(content)

    assert result == content


# ---------------------------------------------------------------------------
# split_sections
# ---------------------------------------------------------------------------

_SINGLE_SECTION = """\
# Document Title

Intro paragraph about the doc.

## Section One

Content for section one with [[some term]].
"""

_TWO_SECTIONS = """\
# Title

Intro text.

## First Section

Content of first section.

## Second Section

Content of second section.
"""

_SECTION_WITH_SUBSECTIONS = """\
## Big Section

Opening paragraph.

### Sub A

Sub A content.

### Sub B

Sub B content.
"""


def test_split_sections_single_section_returns_one_tuple():
    sections = split_sections(_SINGLE_SECTION, 'my-doc')

    assert len(sections) == 1
    slug, content = sections[0]
    assert slug == 'my-doc--section-one'
    assert 'Content for section one' in content


def test_split_sections_prepends_intro_to_first_section():
    sections = split_sections(_SINGLE_SECTION, 'my-doc')

    _, content = sections[0]
    assert 'Intro paragraph about the doc' in content


def test_split_sections_two_sections_returns_two_tuples():
    sections = split_sections(_TWO_SECTIONS, 'my-doc')

    assert len(sections) == 2
    slugs = [s for s, _ in sections]
    assert 'my-doc--first-section' in slugs
    assert 'my-doc--second-section' in slugs


def test_split_sections_intro_only_prepended_to_first():
    sections = split_sections(_TWO_SECTIONS, 'my-doc')

    _, first_content = sections[0]
    _, second_content = sections[1]
    assert 'Intro text' in first_content
    assert 'Intro text' not in second_content


def test_split_sections_no_headings_returns_single_slug_from_doc():
    content = 'Just plain content with no headings.\n'

    sections = split_sections(content, 'plain-doc')

    assert len(sections) == 1
    slug, body = sections[0]
    assert slug == 'plain-doc'
    assert 'Just plain content' in body


def test_split_sections_oversized_section_splits_on_h3(monkeypatch):
    import core.preprocess as preprocess_mod
    monkeypatch.setattr(preprocess_mod, '_MAX_SECTION_CHARS', 50)

    sections = split_sections(_SECTION_WITH_SUBSECTIONS, 'doc')

    slugs = [s for s, _ in sections]
    # subsections namespaced under parent: {doc}--{h2}--{h3}
    assert 'doc--big-section--sub-a' in slugs
    assert 'doc--big-section--sub-b' in slugs


def test_split_sections_slug_uses_double_dash_separator():
    sections = split_sections(_TWO_SECTIONS, 'context-engineering')

    slugs = [s for s, _ in sections]
    assert all('--' in s for s in slugs)
    assert 'context-engineering--first-section' in slugs
