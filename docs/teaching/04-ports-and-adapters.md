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

## "But where does the argument actually come from?"

This is the question that trips up almost everyone the first time they meet this pattern. You look at `get_players(self) -> list[Player]` and think:

- "Where does the data I'm returning _come from_?"
- "I returned a `list[Player]` — where does it _go_?"
- "Who passes in the `db` argument? It's just... there?"

If you're asking these, good — it means you're paying attention. Here's the mental shift that makes it click.

### A function signature is a promise, not a wire

`def get_players(self) -> list[Player]` is a **contract**. It says: _"If you call me, I promise to give you back a list of `Player` objects. I don't know who you are, and you don't need to know how I do it."_ That's the whole deal.

The person _writing_ the adapter only has to keep that promise: produce a `list[Player]`, somehow. They don't worry about who calls it.

The person _calling_ it only relies on the promise: they get a `list[Player]` back. They don't worry about how it was produced.

The two sides never need to know about each other. They only need to agree on the contract. **This is the entire point of the abstraction — and it's also why "where does it come from / go to" feels mysterious: by design, neither side can see the other.** The data doesn't flow through a hidden wire; it flows through ordinary function calls and returns, one frame at a time.

### The composition root: where the wires actually get connected

So if the adapter and the caller never reference each other, _something_ has to introduce them. That something is a small piece of code called the **composition root** — the one place in each program where concrete things get constructed and handed to the code that needs them. It's usually `main()` or the framework's startup.

We have **two** programs, so we have two composition roots — and this is exactly the scraper-as-separate-service idea from [doc 01](01-the-big-picture.md#the-scraper-is-a-separate-service) made concrete:

```python
# services/scraper/__main__.py  — the scraper service's composition root
from libs.python.database.sqlite_adapter import SQLiteAdapter
from scraper.pipeline import run_scraper

def main() -> None:
    db = SQLiteAdapter("data.db")   # ← the concrete adapter is BORN here
    run_scraper(db)                 # ← and handed to code that only knows the port

if __name__ == "__main__":
    main()
```

```python
# apps/backend/main.py  — the backend's composition root
def get_db() -> DatabasePort:
    return SQLiteAdapter("data.db")  # ← a second, independent birth of an adapter
```

Notice: `SQLiteAdapter("data.db")` appears in exactly these two spots and nowhere else. Everything downstream — `run_scraper`, the route handlers — receives a `DatabasePort` as an argument and never names a concrete class. That's why "switching to Postgres later" is a two-line change: you swap the constructor in these two composition roots, and nothing else in the codebase even notices.

### Following one `Player` through the whole system

Here's the part that answers "where does it come from / where does it go." Let's trace the **write path** (the scraper saving data) and the **read path** (the API serving it). Read these top to bottom — each indent is one function call deeper; each `←`/`→` is a value moving.

**Write path — a `Player` is born in the scraper and lands in the database:**

```
main()                                    services/scraper/__main__.py
│
├─ db = SQLiteAdapter("data.db")          the concrete adapter is constructed
│
└─ run_scraper(db)                        db passed in, typed only as DatabasePort
   │
   ├─ players = parse_pages(...)          → list[Player] is produced here
   │                                        (this is where the data "comes from":
   │                                         the parser built it from HTML)
   │
   └─ db.save_players(players)            players handed to the contract method
      │
      └─ SQLiteAdapter.save_players(...)  the CONCRETE code runs (chosen back in main)
         executes INSERT OR REPLACE ...   → the Players land in SQLite. End of journey.
```

**Read path — a `Player` comes out of the database and becomes JSON in the browser:**

```
GET /players                             browser → FastAPI receives the request
│
└─ list_players(db = Depends(get_db))    FastAPI calls get_db() to FILL the db argument
   │                                       (THIS is "where the argument comes from":
   │            ┌─ get_db() → SQLiteAdapter("data.db")   the framework constructs it
   │            │              for you, right before the call)
   │
   ├─ players = db.get_players()         call the contract method
   │  │
   │  └─ SQLiteAdapter.get_players()     concrete code runs: SELECT ... FROM players
   │     returns [Player(...), ...]      → list[Player] is created from DB rows
   │  ←─ list[Player] flows back UP       (this is "where the return value goes":
   │                                        straight back to whoever called it — here,
   │                                        the route handler one frame up)
   │
   └─ return [PlayerResponse(**p.__dict__) for p in players]
      → FastAPI serializes to JSON → HTTP response → browser renders the table
```

The thing to internalize: **an argument "comes from" whoever called the function, and a return value "goes to" whoever called the function.** Nothing more magical than that. The composition root is just the very first caller in the chain — the place where the concrete `SQLiteAdapter` gets created and passed down so that everything below it can work purely in terms of the `DatabasePort` contract.

If you ever lose the thread mid-ticket, find the composition root (`main()` or `get_db()`) and read downward. Every argument deeper in the stack was put there by someone shallower.

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
