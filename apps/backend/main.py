"""ASGI entrypoint: `uv run fastapi dev apps/backend/main.py`."""

from fantasy_futsal_backend.app import app

__all__ = ["app"]
