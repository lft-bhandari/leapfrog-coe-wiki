from __future__ import annotations

import re


def slugify(name: str) -> str:
    """Convert a string to a URL-safe lowercase slug.

    Args:
        name: Any string (filename stem, wikilink term, etc.).

    Returns:
        Lowercase slug with non-alphanumeric runs replaced by hyphens,
        stripped of leading/trailing hyphens. Returns empty string if
        the input has no alphanumeric characters.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    return slug.strip("-")
