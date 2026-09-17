# Coding Standards

Applies to all code in this repo. Agents must follow these when writing or editing code.

---

## Comments

Every non-obvious decision in the code **must** have a one-line comment explaining the constraint or invariant. "Non-obvious" means a future reader familiar with the language and framework would not immediately understand *why* this choice was made.

Do **not** write comments that:
- Restate what the code already says (`# increment counter` above `count += 1`)
- Reference the current task, ticket, or caller (`# added for ingest flow`)
- Explain what a well-named function does

One short line is the maximum. Multi-line comment blocks are not used.

---

## Python

### Docstrings

Use **Google-style docstrings** on all public functions and classes where the signature alone does not communicate the contract. Internal helpers and private functions (`_name`) do not get docstrings.

Format: one-line summary. Add `Args:`, `Returns:`, and `Raises:` sections only when they add information not already clear from type hints — omit them when the types are self-explanatory.

```python
def ingest_doc(
    doc_path: Path,
    wiki_dir: Path,
    synthesize_fn: Callable[[str, str], str],
) -> None:
    """Copy the source file to raw/ and write a synthesized source page to sources/.

    Args:
        doc_path: Path to the local markdown file to ingest.
        wiki_dir: Root of the wiki directory tree (contains raw/ and sources/).
        synthesize_fn: Callable that takes (content, slug) and returns a wiki source page.

    Raises:
        ValueError: If a slug cannot be derived from the filename.
    """
```

For simple cases where the signature is clear, a one-line summary is enough:

```python
def _slugify(name: str) -> str:
    """Convert a filename stem to a URL-safe lowercase slug."""
```

### Type hints

All function signatures must be fully annotated. Use `from __future__ import annotations` for forward references. Prefer `X | None` over `Optional[X]`.

### Design patterns

**Dependency injection over direct import.** Collaborators with side effects (LLM clients, filesystem wrappers, clocks) are injected as arguments, not imported at call sites. This is the pattern established in `scripts/core/ingest_doc.py` (`synthesize_fn` parameter) and must be followed throughout.

```python
# correct
def ingest_doc(doc_path, wiki_dir, synthesize_fn): ...

# wrong
def ingest_doc(doc_path, wiki_dir):
    client = anthropic.Anthropic()  # hidden dependency
```

**Functional core, imperative shell.** Business logic lives in pure functions with no I/O. Side effects (disk writes, API calls, CLI output) are pushed to the edges. The CLI (`ingest.py`) is the shell; `core/` modules are the core.

**No global state.** Module-level variables must be constants (`ALL_CAPS`). Mutable state is initialised inside functions or passed explicitly.

### Style

- `ruff` for formatting and linting (configured at the package level).
- Line length: 100.
- Single quotes for strings unless the string contains a single quote.

---

## TypeScript

### JSDoc

Use JSDoc only on exported functions and React components where the signature is not self-documenting. Skip it for internal utilities and one-liners.

Format: one-line summary. No `@param`/`@returns` tags — TypeScript types carry that information.

```typescript
/** Converts a raw wiki page path to its canonical wikilink form. */
export function toWikilink(path: string): string { ... }
```

### Type annotations

Prefer explicit return types on all exported functions. Avoid `any`; use `unknown` and narrow it. Do not use type assertions (`as X`) to silence the compiler — fix the type instead.

### Design patterns

**Server components by default.** In `apps/web/`, components are React Server Components unless they require browser APIs or interactivity, in which case add `"use client"` at the top.

**Colocate queries with their component.** Data fetching lives next to the component that renders it, not in a global store. Shared data is fetched in a layout or passed as props.

**Named exports over default exports.** Use `export function Foo` not `export default function Foo`. This keeps refactoring safe and grep-friendly.

### Style

- `prettier` for formatting; `eslint` with the project config for linting.
- Semicolons: off (prettier handles ASI).
- Trailing commas: `all`.

---

## Tests

- Tests assert behaviour through public interfaces (seams), not implementation internals.
- Expected values come from independent sources of truth (known literals, worked examples), never recomputed the same way the code does.
- No snapshot tests that encode arbitrary output — only snapshots with known-correct values used as fixtures.
- Mock only at the boundary between your code and an external system (LLM API, filesystem, network). Do not mock internal collaborators.
