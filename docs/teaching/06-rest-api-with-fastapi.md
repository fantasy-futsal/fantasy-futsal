# 06 — REST API with FastAPI

> Read before writing the FastAPI endpoints (#20).

## What an HTTP API is, in our context

The scraper writes data into the database. The frontend wants to show it in a table. Those two pieces don't run in the same process — the scraper is a CLI script, the frontend is a JavaScript app in a browser. They need a way to talk.

The way they talk is **HTTP**: the frontend sends an HTTP request like `GET /players`, our backend receives it, looks up the data via the `DatabasePort`, and returns it as JSON. That backend is a **REST API**, and we're writing it with **FastAPI**.

The simplest possible version of this is one route:

```python
# apps/backend/main.py
from fastapi import FastAPI, Depends
from libs.python.database.port import DatabasePort
from libs.python.database.sqlite_adapter import SQLiteAdapter
from apps.backend.schemas import PlayerResponse

app = FastAPI()

def get_db() -> DatabasePort:
    return SQLiteAdapter("data.db")

@app.get("/players")
def list_players(db: DatabasePort = Depends(get_db)) -> list[PlayerResponse]:
    players = db.get_players()
    return [PlayerResponse(**p.__dict__) for p in players]
```

Run `uv run fastapi dev apps/backend/main.py`, hit `http://localhost:8000/players`, and you get JSON back. That's the whole core idea. The rest of this doc is about why each piece of that snippet looks the way it does.

## Why FastAPI specifically

There are many Python web frameworks (Flask, Django, Starlette, Litestar, ...). We chose FastAPI for four reasons:

1. **Types in, types out.** Your function signatures _are_ the API contract. `def list_players(...) -> list[PlayerResponse]` doesn't just document the return shape — FastAPI uses it to serialize, validate, and document the route.
2. **OpenAPI for free.** FastAPI generates an OpenAPI spec from your types, and serves an interactive UI at `/docs`. You can hit any endpoint from a web form without writing curl commands. (Try it!)
3. **Dependency injection built in.** The `Depends(...)` pattern we use for `DatabasePort` is first-class. No DI framework, no global singletons.
4. **Async-ready.** We won't need it for the MVP, but when we add background jobs and concurrent scraping later, we don't have to change frameworks.

## Anatomy of a route

```python
@app.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: str,
    db: DatabasePort = Depends(get_db),
) -> PlayerResponse:
    player = db.get_player(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerResponse(**player.__dict__)
```

Reading top to bottom:

- **`@app.get("/players/{player_id}")`** — this function handles `GET` requests to that URL pattern. `{player_id}` is a path parameter.
- **`response_model=PlayerResponse`** — what this route returns, as a Pydantic model. FastAPI uses this for validation, serialization, and the auto-generated docs.
- **`player_id: str`** — FastAPI sees this matches the path parameter name and validates that incoming requests have a string there.
- **`db: DatabasePort = Depends(get_db)`** — dependency injection. The framework calls `get_db()` and passes its return value here. Tests can override this; see "Testing" below.
- **`raise HTTPException(...)`** — the right way to return an error response. FastAPI turns this into a proper 404 with a JSON body. Don't return `{"error": "..."}` from the function body — let HTTPException do it.

## Response models — the contract with the frontend

A response model is a Pydantic class that describes the JSON your route returns:

```python
# apps/backend/schemas.py
from pydantic import BaseModel

class PlayerResponse(BaseModel):
    id: str
    name: str
    team: str
    position: str
```

Three things happen because you declared this:

1. The route function's return value is validated against this shape before being sent. If you accidentally return `{"id": 42, ...}`, FastAPI catches it (because `id` is declared `str`) and raises a server error. You find out _now_, not when the frontend silently breaks.
2. The JSON the frontend sees has _exactly_ these fields — nothing extra leaks out. If the internal `Player` dataclass grows a `secret_internal_field`, your `PlayerResponse` doesn't, and the frontend never sees it.
3. The `/docs` page shows the exact schema. Frontend developers (and you, six months from now) can read it without reading the route's source.

This is why we keep `Player` (dataclass, internal) separate from `PlayerResponse` (Pydantic, API-facing) — see [doc 03](03-typed-python.md). The conversion is a single line; the discipline buys you a stable API.

## Dependency injection via `Depends`

Look again:

```python
def get_db() -> DatabasePort:
    return SQLiteAdapter("data.db")

@app.get("/players")
def list_players(db: DatabasePort = Depends(get_db)) -> list[PlayerResponse]:
    ...
```

`Depends(get_db)` is not "call `get_db()` once at startup." It's "before each request, call `get_db()` and pass the result here." This means:

- **Tests can override it.** `app.dependency_overrides[get_db] = lambda: FakeAdapter()` and now every route in your tests uses a fake database. No mocking libraries, no global state surgery.
- **Per-request setup happens at the right place.** If you ever need "open a database transaction for this request and close it after," you put that in `get_db()` with `yield`, and FastAPI handles the lifecycle.
- **The route stays honest about what it depends on.** Looking at the signature alone tells you "this route uses a `DatabasePort`."

The naive alternative — a module-level `db = SQLiteAdapter("data.db")` and `from main import db` in every route — works for a tiny app but binds every route to one specific adapter and makes testing a misery. We start with `Depends` from day one.

## HTTP status codes you'll use

| Code | Meaning | When to return |
|---|---|---|
| 200 | OK | Default for successful GETs |
| 201 | Created | Successful POSTs that created a new resource |
| 204 | No Content | Successful DELETEs |
| 400 | Bad Request | Client sent something that doesn't make sense |
| 404 | Not Found | The requested resource doesn't exist |
| 422 | Unprocessable Entity | Pydantic validation failed (FastAPI does this automatically) |
| 500 | Server Error | Something broke on our side — usually means a bug |

You almost never write `status_code=200` or `status_code=422` yourself. The first is the default; the second is FastAPI's automatic response when an incoming request fails validation. You'll mostly raise `HTTPException(404, ...)` for "not found" cases and let everything else handle itself.

## The `/docs` URL

When FastAPI is running, open `http://localhost:8000/docs` in a browser. You'll see a Swagger UI page listing every route, every response shape, every parameter — generated from your type annotations. You can call any endpoint from a form on that page.

Two things to use this for:

1. **Sanity-check your route signature.** If `/docs` shows your endpoint returning `{}` because you forgot the response model, you'll see it immediately.
2. **Hand it to a frontend developer (or future-you) instead of writing API docs.** The contract _is_ the type annotations; `/docs` just renders them.

## Common pitfalls

### Returning ORM/database objects directly

```python
# Don't:
@app.get("/players")
def list_players(db: DatabasePort = Depends(get_db)) -> list[Player]:
    return db.get_players()  # leaks the internal Player dataclass shape
```

Even though `Player` and `PlayerResponse` look identical right now, returning the dataclass directly means you've coupled the API shape to the internal storage shape. The first time you add an internal-only field to `Player`, your API leaks it. **Always go through the Pydantic response model.**

### Business logic in routes

The route handler should be ten lines or fewer. Its job is "translate HTTP request → call some logic → translate back to HTTP response." If you find yourself writing a scoring algorithm inside a route, move it: it belongs in a service module (`apps/backend/services/scoring.py` or, if shared, `libs/python/scoring/`).

### Unbounded list endpoints

`GET /players` returning all 200 players today is fine. The same endpoint when there are 200,000 records is not. Add pagination (`?limit=...&offset=...`) before the list gets large — not after.

### Hardcoded URLs in the frontend

This is a frontend pitfall but worth flagging: the frontend should never hardcode `http://localhost:8000/players`. Use an environment variable or a SvelteKit `load` function with the configured base URL. See [doc 07](07-frontend-data-flow.md).

## Tickets this prepares you for

- **#20 — Create FastAPI endpoints for players** (yours — start with `GET /players` and `GET /players/{id}`)
- **#26 — Add tests for API endpoints** (use `dependency_overrides` with a fake adapter)
- **M2 tickets (#28, #29)** — scoring rules and points calculation; the routes that expose those will follow the patterns here
