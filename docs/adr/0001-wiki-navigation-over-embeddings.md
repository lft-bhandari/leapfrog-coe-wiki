# Wiki navigation over vector embeddings for retrieval

The standard approach for LLM apps over a document corpus is RAG: embed chunks into a vector store and retrieve by similarity at query time. We chose a different shape: the LLM synthesizes a structured wiki from source docs at ingest time, and queries are answered by navigating that wiki progressively (index → domain → concept/source pages) rather than by embedding search.

## Why

The CoE docs are large and authoritative but few in number — the bottleneck is comprehension, not recall speed. A structured wiki forces the LLM to synthesize and resolve contradictions at ingest time rather than at query time, which produces higher-quality, more coherent answers. The ≥2 rule also means the system surfaces cross-document patterns that a per-query embedding search would miss.

## Considered options

- **RAG with ChromaDB**: simpler to implement, well-understood, scales to large corpora. Rejected because retrieval quality degrades with long authoritative docs, and answers are assembled from chunks without synthesis.
- **Context stuffing (no index)**: load all docs into context on every query. Viable at small scale but hits context limits as the corpus grows, and gives the LLM no structure to navigate.

## Consequences

The wiki must be re-ingested when source docs change. Query quality depends on wiki structure quality; a poorly synthesized wiki produces poor answers. If the corpus grows very large (hundreds of docs), progressive disclosure may need a hybrid approach — but that decision is deferred until the corpus justifies it.
