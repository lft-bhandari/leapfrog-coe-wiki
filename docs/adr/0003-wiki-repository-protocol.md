# WikiRepository Protocol as the filesystem seam

All wiki read/write operations go through a `WikiRepository` Protocol rather than raw `Path` calls scattered across modules. The Protocol is defined in `scripts/core/wiki_repository.py` and duplicated (not shared) in `apps/api/` — it is a type contract, not shared logic.

## Interface

```python
from typing import Protocol
from typing import Literal

PageType = Literal["sources", "concepts", "entities", "domains"]

class WikiRepository(Protocol):
    def write_raw(self, slug: str, content: str) -> None: ...
    def write_page(self, page_type: PageType, slug: str, content: str) -> None: ...
    def read_page(self, page_type: PageType, slug: str) -> str: ...
    def list_slugs(self, page_type: PageType) -> list[str]: ...
    def page_exists(self, page_type: PageType, slug: str) -> bool: ...
```

`PageType` is a `Literal` alias, not an Enum — mypy catches typos at type-check time with no runtime ceremony.

## Why

Ticket 4 (synthesis) needs to read back existing pages to apply the ≥2 rule. Without a repository, synthesis modules mix Path manipulation with business logic, making them untestable without a real filesystem. A Protocol lets tests inject a lightweight fake.

`typing.Protocol` (structural) is used over `abc.ABC` (nominal) because fakes in tests need no inheritance chain — any class with the right methods satisfies the contract.

## Considered options

- **Raw `Path` calls everywhere**: simpler initially, but synthesis logic becomes untestable in isolation as soon as it reads back existing pages.
- **Shared `packages/wiki-core/` package**: the canonical long-term home, but the overhead of a third Python package outweighs the benefit at this stage. Revisit if shared logic beyond the Protocol emerges.

## Consequences

`ingest_doc` will be updated to accept a `WikiRepository` instead of `wiki_dir: Path`. The real `FilesystemWikiRepository` implementation lives alongside the Protocol in `scripts/core/`. `apps/api/` defines its own copy of the Protocol — keep them in sync by hand; they are small.
