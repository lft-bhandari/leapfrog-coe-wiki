from fastapi import FastAPI

from app.routers import chat, graph, wiki

app = FastAPI(title="CoE Wiki API")
app.include_router(graph.router)
app.include_router(chat.router)
app.include_router(wiki.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
