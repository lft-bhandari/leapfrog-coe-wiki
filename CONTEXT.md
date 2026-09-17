# CoE Wiki

An LLM-powered internal knowledge base that lets Leapfrog employees ask questions about CoE research and get cited answers, without reading large documents in full.

## Language

### The wiki

**Wiki**: The structured knowledge base built from ingested CoE docs. Two halves that never mix: `raw/` and `wiki/`.
_Avoid_: Knowledge base, index, database

**Raw**: The immutable copy of a source document as ingested. Written once, never edited by the system.
_Avoid_: Original, source file, input

**Wiki page**: An LLM-synthesized markdown file in `wiki/`. Pages carry YAML frontmatter and cite their sources via wikilinks.
_Avoid_: Article, document, note

**Wikilink**: A `[[path/to/page]]` reference inside a wiki page pointing to another wiki page. Wikilinks are the edges of the knowledge graph.
_Avoid_: Link, reference, citation

**The ≥2 rule**: A concept or entity page is created only when two or more distinct sources engage with that term. One source mentioning a concept is a fact about that source; two sources makes it a fact about the knowledge base.
_Avoid_: Threshold, minimum mentions

### Page types

**Domain page**: A hub page representing one of the 8 AI roadmap sections (or `general/` for non-AI CoE docs). Domain pages are the top-level clusters in the knowledge graph.
_Avoid_: Category, section, topic group

**Concept page**: A synthesized page for a topic that appears in ≥2 sources. Lives under `wiki/concepts/`.
_Avoid_: Topic page, idea page

**Entity page**: A page for a named thing — tool, framework, standard, organisation — that appears in ≥2 sources. Lives under `wiki/entities/`.
_Avoid_: Named entity, proper noun page

**Source page**: One page per ingested CoE document, summarising its key claims with wikilinks to the concepts and entities it touches. Lives under `wiki/sources/`.
_Avoid_: Doc page, article page, summary page

### Ingest and query

**Ingest**: The process of pulling a Google Doc from Drive, writing it to `raw/`, and synthesizing or updating wiki pages. Triggered manually via CLI.
_Avoid_: Sync, import, load, crawl

**Progressive disclosure**: The query strategy: the LLM starts at `index.md`, walks to the relevant domain index, then to concept/entity pages, then to source pages, and reaches `raw/` only as a last resort.
_Avoid_: Navigation, traversal, search

**The graph view**: The React Flow visualisation of the wiki as an interactive node graph. Domain pages are hub nodes; concept, entity, and source pages connect to them via wikilinks.
_Avoid_: Knowledge graph UI, graph visualisation, network view

### The roadmap

**Roadmap domain**: One of the 8 top-level sections of the Leapfrog AI Learning Roadmap (Gen AI Fundamentals, Retrieval and Knowledge, Agents and Autonomy, Evaluation and Quality, Models, Security and Governance, Platform and Operations, Classical ML). Each is a hub node in the graph.
_Avoid_: Category, pillar, track

**General**: The catch-all domain for CoE docs that don't map to the 8 AI roadmap sections (e.g. coding guidelines, project retrospectives).
_Avoid_: Other, misc, uncategorised
