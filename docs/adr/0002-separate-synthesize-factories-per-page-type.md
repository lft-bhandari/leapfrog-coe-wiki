# Separate synthesize factory per wiki page type

The `synthesize_fn` seam is `Callable[[str, str], str]` throughout the codebase. Different wiki page types (source, concept, entity, domain) require different prompts. Rather than adding a `page_type` parameter to the callable or baking branching into a single factory, each page type gets its own factory function: `make_source_synthesize_fn`, `make_concept_synthesize_fn`, `make_entity_synthesize_fn`, `make_domain_synthesize_fn`.

## Why

Keeping the seam shape identical across all page types means `ingest_doc` and future synthesis modules stay unchanged when new page types are added. Each factory is independently testable. Prompt logic for one page type cannot accidentally affect another.

## Considered options

- **Page type enum in the callable** — `Callable[[str, str, PageType], str]`. Rejected: leaks page-type knowledge into every caller and makes the seam harder to mock in tests.
- **Prompt as a factory parameter** — `make_synthesize_fn(client, prompt)`. Rejected: callers must know which prompt string to pass, which is the same coupling problem one level up.

## Consequences

Adding a new page type requires a new factory function in `core/synthesize.py`. The prompt for each type is co-located with its factory, so it is easy to find and change. All factories share the same guards (stop_reason, block type check) — these should be extracted into a shared internal helper if they diverge.
