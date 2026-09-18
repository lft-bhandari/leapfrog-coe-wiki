from __future__ import annotations

import re
from dataclasses import dataclass

from core.slug import slugify

_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)\n?')
_H2_RE = re.compile(r'^## (.+)$', re.MULTILINE)
_H3_RE = re.compile(r'^### (.+)$', re.MULTILINE)

# ~37k tokens; leaves headroom within a 200k-token model context window
_MAX_SECTION_CHARS = 150_000


@dataclass
class Section:
    """A named chunk of a document ready for LLM synthesis."""

    slug: str
    content: str


def strip_images(content: str) -> str:
    """Remove all markdown image references from content.

    Args:
        content: Raw markdown text.

    Returns:
        Content with every ![alt](url) occurrence removed.
    """
    return _IMAGE_RE.sub('', content)


def _split_by_heading(
    content: str,
    heading_re: re.Pattern[str],
    doc_slug: str,
    intro: str = '',
) -> list[Section]:
    parts = heading_re.split(content)
    # split() on a capturing group gives: [pre, title1, body1, title2, body2, ...]
    pre = parts[0]
    combined_intro = (intro + pre).strip()

    sections: list[Section] = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ''
        slug = f'{doc_slug}--{slugify(title)}'
        section_content = f'## {title}\n\n{body}'.strip()
        if i == 1 and combined_intro:
            section_content = combined_intro + '\n\n' + section_content
        sections.append(Section(slug=slug, content=section_content))

    return sections


def split_sections(content: str, doc_slug: str) -> list[Section]:
    """Split a markdown document into per-section chunks suitable for LLM synthesis.

    Splits on ## headings first. Any section exceeding _MAX_SECTION_CHARS is
    further split on ### subheadings. Content before the first ## is prepended
    to the first section. A document with no ## headings is returned as-is under
    the doc_slug.

    Args:
        content: Markdown document text (images should already be stripped).
        doc_slug: Slug of the parent document, used to namespace section slugs.

    Returns:
        List of Section objects. Section slugs use the pattern
        ``{doc_slug}--{section_slug}``.
    """
    if not _H2_RE.search(content):
        return [Section(slug=doc_slug, content=content.strip())]

    raw_sections = _split_by_heading(content, _H2_RE, doc_slug)

    result: list[Section] = []
    for section in raw_sections:
        if len(section.content) <= _MAX_SECTION_CHARS or not _H3_RE.search(section.content):
            result.append(section)
        else:
            # Strip the ## heading so _split_by_heading handles ### cleanly,
            # passing the ## line as the intro to preserve context.
            first_line_end = (
                section.content.index('\n') if '\n' in section.content else len(section.content)
            )
            h2_line = section.content[:first_line_end]
            remainder = section.content[first_line_end + 1:]
            sub_sections = _split_by_heading(remainder, _H3_RE, section.slug, intro=h2_line)
            if sub_sections:
                result.extend(sub_sections)
            else:
                result.append(section)

    return result
