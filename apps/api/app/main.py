from fastapi import FastAPI

from app.routers import graph

app = FastAPI(title="CoE Wiki API")
app.include_router(graph.router)


@app.get("/health")
def health():
    return {"status": "ok"}
