from fastapi import FastAPI

app = FastAPI(title="CoE Wiki API")


@app.get("/health")
def health():
    return {"status": "ok"}
