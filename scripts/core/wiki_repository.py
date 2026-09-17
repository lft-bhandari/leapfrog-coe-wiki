from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol


PageType = Literal["sources", "concepts", "entities", "domains"]


class WikiRepository(Protocol):
    """Filesystem-agnostic interface for reading and writing wiki pages.

    All wiki I/O goes through this Protocol so that synthesis modules
    can be tested without touching the real filesystem.
    """

    def write_raw(self, slug: str, content: str) -> None:
        """Write an immutable copy of a source document to raw/.

        Args:
            slug: URL-safe identifier derived from the source filename.
            content: Full text of the source document.
        """
        ...

    def write_page(self, page_type: PageType, slug: str, content: str) -> None:
        """Write a wiki page under wiki/<page_type>/<slug>.md.

        Args:
            page_type: One of "sources", "concepts", "entities", "domains".
            slug: URL-safe identifier for this page.
            content: Full markdown content including YAML frontmatter.
        """
        ...

    def read_page(self, page_type: PageType, slug: str) -> str:
        """Read an existing wiki page.

        Args:
            page_type: One of "sources", "concepts", "entities", "domains".
            slug: URL-safe identifier for the page.

        Returns:
            Full markdown content of the page.

        Raises:
            FileNotFoundError: If the page does not exist.
        """
        ...

    def list_slugs(self, page_type: PageType) -> list[str]:
        """List all slugs of a given page type.

        Args:
            page_type: One of "sources", "concepts", "entities", "domains".

        Returns:
            Sorted list of slug strings (without .md extension).
        """
        ...

    def page_exists(self, page_type: PageType, slug: str) -> bool:
        """Check whether a wiki page exists.

        Args:
            page_type: One of "sources", "concepts", "entities", "domains".
            slug: URL-safe identifier to check.

        Returns:
            True if the page file exists on disk.
        """
        ...


class FilesystemWikiRepository:
    """Real filesystem implementation of WikiRepository.

    Args:
        wiki_dir: Root directory of the wiki (contains raw/, sources/, etc.).
    """

    def __init__(self, wiki_dir: Path) -> None:
        self._root = wiki_dir

    def write_raw(self, slug: str, content: str) -> None:
        path = self._root / "raw" / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def write_page(self, page_type: PageType, slug: str, content: str) -> None:
        path = self._root / page_type / f"{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def read_page(self, page_type: PageType, slug: str) -> str:
        return (self._root / page_type / f"{slug}.md").read_text()

    def list_slugs(self, page_type: PageType) -> list[str]:
        directory = self._root / page_type
        if not directory.exists():
            return []
        # Sort for deterministic ordering across filesystems
        return sorted(p.stem for p in directory.glob("*.md"))

    def page_exists(self, page_type: PageType, slug: str) -> bool:
        return (self._root / page_type / f"{slug}.md").exists()
