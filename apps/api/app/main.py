from fastapi import FastAPI

from app.routers import chat, graph

app = FastAPI(title="CoE Wiki API")
app.include_router(graph.router)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
