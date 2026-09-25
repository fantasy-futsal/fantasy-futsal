"""Entrypoint: `uv run python -m backend` starts the API server."""

import uvicorn


def main() -> None:
    """Serve the Fantasy Futsal API with uvicorn."""
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
