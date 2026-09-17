from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["wiki"])

_WIKI_DIR = Path(os.environ.get("WIKI_DIR", Path(__file__).parent.parent.parent.parent.parent / "wiki"))
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


class WikiPage(BaseModel):
    path: str
    title: str
    content: str


def _parse_title(content: str, fallback: str) -> str:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return fallback
    for line in match.group(1).splitlines():
        if line.startswith("title:"):
            return line[len("title:"):].strip()
    return fallback


@router.get("/wiki/{path:path}", response_model=WikiPage)
def get_wiki_page(path: str) -> WikiPage:
    """Return the content and metadata of a wiki page by its path.

    Args:
        path: Wiki-relative path without extension, e.g. 'concepts/rag'.

    Raises:
        HTTPException: 404 if the page does not exist in the wiki directory.
    """
    page_file = _WIKI_DIR / f"{path}.md"
    if not page_file.exists():
        raise HTTPException(status_code=404, detail=f"Wiki page '{path}' not found")
    content = page_file.read_text(encoding="utf-8")
    title = _parse_title(content, fallback=path.split("/")[-1])
    # Strip frontmatter before returning so the caller gets the body only
    body = _FRONTMATTER_RE.sub("", content, count=1).strip()
    return WikiPage(path=path, title=title, content=body)
