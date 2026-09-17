# Leapfrog CoE Wiki

An LLM-powered internal knowledge base that lets Leapfrog employees ask questions about CoE research and get cited answers, without reading large documents in full.

- **Chat** — ask a question, get a synthesised answer with citations
- **Graph view** — explore how topics connect across the CoE corpus (React Flow)
- **No embeddings** — the wiki structure is the retrieval mechanism (see `docs/adr/0001-wiki-navigation-over-embeddings.md`)

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | ≥18 | [nodejs.org](https://nodejs.org) |
| Python | ≥3.12 | [python.org](https://python.org) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Ollama | latest | [ollama.com](https://ollama.com) |

Pull the required model:
```bash
ollama pull llama3.2:3b
```

## Running locally

### API (FastAPI)

```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/health`

### Web (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

Opens at `http://localhost:3000`

### Ingest CLI

```bash
cd scripts
uv run python ingest.py <google-doc-url-or-local-file>
```

## Project layout

```
leapfrog-coe-wiki/
├── apps/
│   ├── web/          # Next.js — chat UI + graph view
│   └── api/          # FastAPI — wiki navigation, LLM, graph data
├── wiki/             # gitignored — raw/ and wiki/ markdown files
├── scripts/          # ingest CLI
└── docs/
    ├── agents/       # issue tracker, triage labels, domain docs
    └── adr/          # architecture decision records
```

See `CONTEXT.md` for the domain vocabulary used throughout the project.
