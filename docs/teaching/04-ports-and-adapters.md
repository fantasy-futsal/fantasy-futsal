# 04 — Ports and Adapters

> This is the single most important architectural idea in the project. If you only read one teaching doc, read this one.

## The problem

Imagine you write your scraper, your API, and your frontend assuming the database is SQLite. SQLite is great for local development: it's a single file, no server to run, fast enough. So you sprinkle SQL queries through your code:

```python
# DON'T do this
import sqlite3

def get_players():
    conn = sqlite3.connect("data.db")
    rows = conn.execute("SELECT id, name, team FROM players").fetchall()
    return [Player(id=r[0], name=r[1], team=r[2]) for r in rows]
```

Six months later you want to deploy to production. SQLite doesn't fit — you need something multi-user, hosted, with backups. You decide on Firestore (a Google Cloud NoSQL database). Now you have to **find every place in the codebase that touches SQLite and rewrite it**. Every `conn.execute(...)`, every SQL string, every assumption about rows-and-columns-vs-documents. You probably miss a few. The bugs are subtle.

This is the cost of letting database details leak everywhere.

## The solution, in three lines

1. Define _the shape_ of database operations once, in plain Python, with no SQLite or Firestore code in it.
2. Write a SQLite class that has that shape.
3. Later, write a Firestore class that has the same shape.

Everything else in the codebase — the scraper, the API — only ever talks to "something with that shape." It never knows which one. Switching is one line of configuration.

The "shape" is the **port**. The SQLite and Firestore classes are **adapters** for that port. Hence the name: ports and adapters (sometimes called hexagonal architecture, but the name is less important than the idea).

## The port: a `Protocol`

In Python, the cleanest way to write "the shape" is `typing.Protocol`:

```python
# libs/python/database/port.py
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Player:
    id: str
    name: str
    team: str
    position: str


class DatabasePort(Protocol):
    def save_players(self, players: list[Player]) -> None: ...
    def get_players(self) -> list[Player]: ...
    def get_player(self, player_id: str) -> Player | None: ...
```

A few things worth pausing on:

- **`Protocol` is structural typing**, also called "duck typing made explicit." Any class that happens to have those three methods with those signatures _is_ a `DatabasePort`. You don't have to inherit from it. You don't have to register it. The type checker (mypy) figures it out.
- **`...` is the actual body of the method.** In a Protocol, you're declaring the signature, not implementing anything. `...` is Python's "I literally mean nothing goes here."
- **`Player` is a plain `@dataclass`**, not a SQLite row, not a Firestore document. It is a domain object. The port speaks in domain objects, not storage objects. This is the line you must not cross — see "Common pitfalls" below.

### Aside: `@runtime_checkable`

You can decorate a Protocol with `@runtime_checkable` (from `typing`) and then `isinstance(thing, DatabasePort)` will work at runtime, not just during type checking. With mypy doing the heavy lifting we mostly don't need this, but it's cheap insurance for code that crosses module boundaries — for example, a factory function that loads adapter classes dynamically. The one gotcha: `@runtime_checkable` only verifies that the method _names_ exist on the object, not that their signatures match. mypy still has to catch that part.

## The adapter: SQLite

Now we write an actual implementation. This is **your ticket #19**, so we'll sketch it, not finish it.

```python
# libs/python/database/sqlite_adapter.py
import sqlite3
from libs.python.database.port import DatabasePort, Player


class SQLiteAdapter:
    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                team TEXT NOT NULL,
                position TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def save_players(self, players: list[Player]) -> None:
        self._conn.executemany(
            "INSERT OR REPLACE INTO players (id, name, team, position) VALUES (?, ?, ?, ?)",
            [(p.id, p.name, p.team, p.position) for p in players],
        )
        self._conn.commit()

    def get_players(self) -> list[Player]:
        rows = self._conn.execute("SELECT id, name, team, position FROM players").fetchall()
        return [Player(id=r[0], name=r[1], team=r[2], position=r[3]) for r in rows]

    def get_player(self, player_id: str) -> Player | None:
        row = self._conn.execute(
            "SELECT id, name, team, position FROM players WHERE id = ?",
            (player_id,),
        ).fetchone()
        return Player(id=row[0], name=row[1], team=row[2], position=row[3]) if row else None
```

Notice:

- `SQLiteAdapter` does **not** inherit from `DatabasePort`. It doesn't need to. The Protocol lets us say "anything with this shape qualifies." Adding `class SQLiteAdapter(DatabasePort)` would not be wrong, but it would not be necessary either, and we keep it out for clarity.
- All SQL lives **inside this file**. Nothing leaks. If you want to know what SQL we run, this is the only place to look.
- The methods take and return `Player` (the domain object), not rows or tuples. The translation happens at the edge of the adapter — that's the adapter's whole job.

## The adapter: Firestore (later, ticket #33)

When we add Firestore later, the file looks roughly like this — same shape, different innards:

```python
# libs/python/database/firestore_adapter.py
from google.cloud import firestore
from libs.python.database.port import DatabasePort, Player


class FirestoreAdapter:
    def __init__(self, project_id: str) -> None:
        self._client = firestore.Client(project=project_id)
        self._players = self._client.collection("players")

    def save_players(self, players: list[Player]) -> None:
        batch = self._client.batch()
        for p in players:
            batch.set(self._players.document(p.id), {
                "name": p.name, "team": p.team, "position": p.position,
            })
        batch.commit()

    def get_players(self) -> list[Player]:
        return [
            Player(id=doc.id, **doc.to_dict())
            for doc in self._players.stream()
        ]

    def get_player(self, player_id: str) -> Player | None:
        doc = self._players.document(player_id).get()
        return Player(id=doc.id, **doc.to_dict()) if doc.exists else None
```

Different storage technology, different code _inside_ the methods, **same shape on the outside**. That is the entire payoff.

## How the API uses the port

The FastAPI code (ticket #20) doesn't pick `SQLiteAdapter` or `FirestoreAdapter` directly. It asks for "a `DatabasePort`" and is given one at startup:

```python
# apps/backend/main.py (sketch)
from fastapi import FastAPI, Depends
from libs.python.database.port import DatabasePort, Player
from libs.python.database.sqlite_adapter import SQLiteAdapter

app = FastAPI()

def get_db() -> DatabasePort:
    # The ONE line that picks which adapter to use.
    return SQLiteAdapter("data.db")

@app.get("/players")
def list_players(db: DatabasePort = Depends(get_db)) -> list[Player]:
    return db.get_players()
```

When we move to Firestore, we change `get_db()` and **nothing else**. The route handler doesn't care.

This pattern — pass the dependency in rather than constructing it inside — is called **dependency injection**. FastAPI has first-class support for it via `Depends`. You'll see this pattern a lot.

## Common pitfalls

### Leaking storage details into the port

The Protocol talks in `Player`, not in SQL or Firestore documents. If you ever feel tempted to write:

```python
class DatabasePort(Protocol):
    def execute_sql(self, query: str) -> list[tuple]: ...   # DON'T
```

...you have lost the entire point. The whole reason the port exists is to hide SQL from everyone above it. If callers can pass SQL strings through the port, you've built a slightly more annoying way to call sqlite3 directly. The Firestore adapter would have nowhere to send the SQL string. The abstraction is dead.

**The rule:** every method on the port speaks in domain objects and domain verbs (`get_player`, `save_players`). Never in storage verbs (`execute_sql`, `set_document`).

### Putting business logic in the adapter

The adapter's job is _translation_ between domain objects and storage. It is **not** the place for "if the player's name starts with X, do Y." Business rules live above the port (in the API layer or a dedicated service), not below it. Otherwise switching adapters means re-implementing the rules, which defeats the point.

### Not freezing the dataclass

`@dataclass(frozen=True)` makes `Player` immutable. This matters because once a `Player` leaves the adapter, lots of code might hold references to it. If anyone could mutate it, you'd get the worst kind of bug: a value that quietly changes after you've stored it. Freeze it. (And get free `__hash__` so you can put players in a set.)

## Tickets this prepares you for

- **#18 — Define database port/interface** (mentor task, but read this so you understand what gets written and why)
- **#19 — Implement SQLite adapter** (yours — the SQLite code above is a sketch; the real one needs proper schema for all entities, not just Player)
- **#21 — Wire scraper to database adapter** (the scraper writes through the port, not directly to SQLite)
- **#33 — Implement Firestore adapter** (much later — by then this doc will feel obvious)
