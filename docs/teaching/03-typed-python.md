# 03 — Typed Python

> Read before defining data models (#16). Sets up everything you'll do in `libs/python/`.

## The shift you're about to make

Plain Python lets you do this:

```python
def get_player(player_id):
    # what is player_id? a str? an int? a UUID?
    # what does this return? a dict? a tuple? None?
    # who knows. read the body. read the callers. guess.
    ...
```

Typed Python makes you do this:

```python
def get_player(player_id: str) -> Player | None:
    ...
```

The runtime behavior is the same. The difference is that now an editor, a type checker (mypy), and a future reader (you, in six months) can all answer "what does this take and return?" without reading the function body.

In this project **everything is typed**, and `mypy --strict` runs in CI. That sounds intimidating; it is not. The strict mode rejects code that hides its intent. When you fix what mypy complains about, you almost always discover you _wanted_ to write the typed version anyway, you just hadn't slowed down enough to say so.

## Type hints, the quick version

Modern Python (3.9+) syntax — we don't use the old `typing.List`/`typing.Dict` style:

```python
def example(
    name: str,                 # primitive
    age: int,
    teams: list[str],          # list of strings
    scores: dict[str, int],    # dict from name to score
    nickname: str | None,      # string OR None (the "Maybe" type)
) -> bool:                     # returns True or False
    ...
```

A few patterns that show up everywhere:

- `T | None` for "this might be missing." Always handle both branches at the caller — don't pretend `None` won't happen.
- `list[T]` rather than `List[T]`. The old `typing.List` is legacy.
- For function-as-argument, use `Callable[[arg_types], return_type]` from `collections.abc`.

## Three tools, three jobs

In this codebase you'll meet three ways to describe shapes of data. They look similar but solve different problems. Picking the wrong one is the #1 source of confusion.

| Tool | Use for | Validates at runtime? |
|---|---|---|
| `@dataclass` | Internal domain objects (Player, Team, Match) | No |
| `pydantic.BaseModel` | Data crossing a trust boundary (API requests, scraped HTML) | Yes |
| `typing.Protocol` | Interface contracts (DatabasePort, ScraperPort) | No (unless `@runtime_checkable`) |

### Dataclass — your default

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Player:
    id: str
    name: str
    team: str
    position: str
```

`@dataclass` generates `__init__`, `__repr__`, `__eq__` from the annotations. `frozen=True` makes instances immutable (`p.name = "X"` raises) and gives you `__hash__` for free.

**Why immutable?** Once a `Player` leaves the function that built it, lots of code might hold a reference. If anyone could mutate it, you'd get bugs where a value changes after you stored it. The default in this project is "frozen dataclass unless you have a good reason."

**Dataclasses do NOT validate.** This is fine and intentional:

```python
Player(id=42, name="", team=None, position="???")
# Runs without complaint. mypy --strict will yell at compile time.
# But at runtime, garbage in, garbage out.
```

That's why we use dataclasses for _internal_ objects (we trust the code that constructs them) and switch to Pydantic at the edges.

### Pydantic — for trust boundaries

A "trust boundary" is anywhere data enters our system from somewhere we don't control:

- An HTTP request from a browser
- An HTML page scraped from futsalvplzni.cz
- A JSON file from disk (after the first run, even our own file is "untrusted" because anyone could edit it)

At those boundaries, you want **runtime validation** — actual checks that the data has the shape you expect, with helpful errors when it doesn't. That's Pydantic:

```python
from pydantic import BaseModel, Field

class PlayerResponse(BaseModel):
    id: str
    name: str = Field(min_length=1)
    team: str
    position: str
    goals: int = Field(ge=0)  # ge = "greater or equal" — no negative goals

# This raises pydantic.ValidationError with a useful message:
PlayerResponse.model_validate({"id": "p1", "name": "", "team": "X", "position": "GK", "goals": -2})
```

FastAPI integrates with Pydantic — your route signatures use these models and FastAPI handles the validation + JSON serialization automatically.

**Rule of thumb:** every byte that crosses the network or comes from a file should pass through a Pydantic model on the way in. Convert it to a plain dataclass once you're past the boundary if you want.

### Protocol — for interface contracts

A `Protocol` describes "the shape of an object" without forcing inheritance. It's how we say "the API doesn't care which database implementation it gets, as long as it has these methods." [Doc 04](04-ports-and-adapters.md) is entirely about this idea — here we just place it next to the dataclass and Pydantic so you can see how the three relate.

Use a `Protocol` when you have **multiple implementations** of the same conceptual thing (SQLite vs Postgres vs in-memory fake for tests). For a thing with one implementation, just use the class directly — don't write a Protocol for it.

## A common confusion: dataclass vs Pydantic for the same domain

A natural question: "If I have a `Player`, do I write one dataclass _and_ one Pydantic model, or just one of them?"

Our answer in this project: **two types, one each.**

```python
# libs/python/database/port.py  — internal, no validation
@dataclass(frozen=True)
class Player:
    id: str
    name: str
    team: str
    position: str

# apps/backend/schemas.py  — API boundary, validates on the wire
class PlayerResponse(BaseModel):
    id: str
    name: str
    team: str
    position: str
```

Yes, this is _slight_ duplication. The payoff: the internal `Player` can evolve without breaking the public API, and the public API can change response shape (renaming fields, adding computed fields) without churning the internal model. The conversion between them is a one-liner.

If you _really_ want one type, Pydantic v2's models are dataclass-like and can sometimes serve both roles. Don't reach for that yet — start with the two-type pattern; collapse later if duplication becomes painful.

## What mypy --strict will catch you on

A few things `mypy --strict` flags that vanilla mypy doesn't:

1. **Functions without annotations.** Every function body must declare its arguments and return type. `def foo():` is a hard error.
2. **`Any` leaking through.** If you import something untyped, you get an `Any`, and using it in a strict-typed function fails. The fix is usually to add a `# type: ignore[no-untyped-import]` for the third-party module (sparingly) or to type-stub it.
3. **Missing return statements.** If your function says `-> int` but a branch falls off the end, that's an error.
4. **Optional handling.** If a value is `T | None`, you can't use it as a `T` until you check `if x is None`.

When mypy complains, **the fix is almost always in your code, not in mypy's config**. The first instinct of every Python developer learning strict typing is "let me suppress this with `Any`." Resist. Most of the time, fixing it properly takes one extra line and prevents a real bug.

## Imports — the right way

In this monorepo, after `uv sync` has set up the workspace, your imports look like:

```python
# In apps/backend/backend/app.py
from libs.python.database.port import DatabasePort, Player
from libs.python.database.sqlite_adapter import SQLiteAdapter
```

If you see code or instructions that suggest any of the following, **stop**:

- `sys.path.append("...")`
- `os.environ["PYTHONPATH"] = "..."`
- A `conftest.py` at the root whose only purpose is `sys.path` manipulation
- Bare relative imports like `from ..port import Player` outside of a properly declared package

These are workarounds for not having set up packaging properly. The right fix is upstream: the package should be declared in the workspace, and `uv sync` should install it. If imports don't work after `uv sync`, the workspace config is wrong, not your imports.

## Tickets this prepares you for

- **#16 — Define data models for Player, Team, Match, Stats** (yours — apply the dataclass-for-internal, Pydantic-for-boundary rule)
- **#18 — Define database port/interface** (mentor task, but you should read the Protocol section before that review)
- **#20 — FastAPI endpoints** (the response models there are Pydantic)
- **#17 — Web scraper** (Pydantic models validate the scraped data at the boundary)
