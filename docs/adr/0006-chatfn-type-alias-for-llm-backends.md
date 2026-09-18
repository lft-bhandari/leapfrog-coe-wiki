# ChatFn type alias as the seam for LLM backends in the scripts layer

The synthesis factories (`make_source_synthesize_fn`, `make_term_synthesize_fn`) accept a `chat_fn` parameter of type `ChatFn = Callable[[str, str], str]` — a function from `(system_prompt, user_message)` to a reply string. Concrete backends (`make_ollama_chat_fn`, and future ones such as Bedrock) are factory functions that return a `ChatFn`. `ingest.py` constructs the backend and passes it in.

## Why

Adding a second LLM provider (AWS Bedrock) required extracting the Ollama HTTP call from inside the synthesize factories. A type alias keeps the seam minimal: one line, no inheritance, no runtime ceremony. Every synthesize factory stays unchanged as new backends are added; only `ingest.py` selects which factory to construct.

## Considered options

- **`typing.Protocol` with a `.chat(system, user)` method**: named contract, documentable, `isinstance`-checkable. Rejected because the factories are already the unit of composition — there is no need to name an intermediate object. The alias catches the same type errors at check time with less machinery.
- **`page_type` enum parameter on a single factory**: leaks backend knowledge into callers. Rejected for the same reason as ADR-0002.
- **Env-var branch inside the existing factories**: avoids a new module but couples provider logic to prompt logic. Rejected to keep each factory focused on its prompt.

## Consequences

Adding a new provider means implementing `make_<provider>_chat_fn() -> ChatFn` in `core/chat_backends.py` and adding a branch in `ingest.py`. The synthesize factories and all their tests are unaffected. The `ChatFn` alias lives in `core/chat_backends.py`, which is the sole place that contains provider-specific HTTP calls in the scripts layer.
