"""Application factory and route definitions for the Fantasy Futsal backend."""

from fastapi import FastAPI

app = FastAPI(title="Fantasy Futsal API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by infrastructure and smoke tests."""
    return {"status": "ok"}
