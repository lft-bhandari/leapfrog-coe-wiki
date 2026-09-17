# FastAPI: APIRouter per domain + service layer via Depends()

`apps/api/` is structured as one `APIRouter` per domain (`routers/query.py`, `routers/graph.py`), each mounted in `main.py`. Business logic lives in `app/services/` (`QueryService`, `GraphService`) and is injected into routers via FastAPI's `Depends()`.

## Structure

```
apps/api/app/
  main.py              # mounts routers, creates app
  routers/
    query.py           # HTTP: POST /query, GET /stream
    graph.py           # HTTP: GET /graph
  services/
    query_service.py   # QueryService — wiki navigation logic
    graph_service.py   # GraphService — graph edge assembly
```

## Why

Keeping HTTP concerns (request parsing, status codes, streaming responses) out of business logic makes `QueryService` and `GraphService` unit-testable without spinning up a server. FastAPI's `Depends()` is the idiomatic way to inject collaborators and supports overriding in tests via `app.dependency_overrides`.

## Considered options

- **Flat `main.py`**: viable for a single endpoint, collapses under two real domains.
- **Routers without a service layer**: routers handle business logic directly. Rejected: business logic becomes entangled with HTTP, hard to test in isolation.

## Consequences

Each new domain requires a router file and a service class. Services must not import FastAPI types — they are plain Python classes. The `WikiRepository` (see ADR-0003) is injected into services via `Depends()`.
