# 05 — Scraping Defensively

> Read before researching futsalvplzni.cz (#15) and writing the scraper (#17).

## The mindset

A web scraper is a program that reads pages from a website you don't own and extracts data from them. That sentence contains two assumptions you must drop immediately:

1. ~~The HTML will be well-formed and consistent.~~ It won't. Different pages have different layouts. Some pages are broken. Some have ads injected. Some redirect.
2. ~~The HTML you see today is the HTML you'll see tomorrow.~~ The website owner can redesign at any time without telling you. Your scraper that worked yesterday will silently produce garbage today.

Writing a scraper is the act of negotiating with **hostile input** — not maliciously hostile, just unreliable. Every scraping problem you'll hit reduces to "I assumed something about the HTML that isn't true." The fix is always to assume less and check more.

## The pipeline pattern

A naive scraper does this in one function:

```python
# Don't.
def scrape_and_save():
    html = requests.get(URL).text
    players = parse(html)
    db.save_players(players)
```

This works once. It is painful for every other run. If `db.save_players` fails, you re-fetch the HTML; if the website is slow that's minutes you didn't need to spend. If `parse` has a bug, you re-fetch _again_ to debug it. If something looks wrong in the database, you have no way to inspect what HTML produced it.

The pattern we use instead is **three discrete stages with a checkpoint between fetch and parse**:

```
  ┌─────────────┐   ┌──────────────┐   ┌────────────────┐
  │  1. Fetch   │ → │  2. Parse    │ → │  3. Load to DB │
  │   (HTTP)    │   │   (HTML →    │   │   (via the     │
  │             │   │    objects)  │   │   port)        │
  └──────┬──────┘   └──────┬───────┘   └────────────────┘
         │                 │
         ▼                 ▼
   raw HTML on disk   typed JSON on disk
   (cache/*.html)     (data/players.json)
```

Each arrow can be re-run without re-running the one before it. That changes the development experience dramatically: a parse bug is a 200ms iteration loop reading from disk, not a 10-second network round-trip.

In code:

```python
def fetch() -> None:
    """Stage 1: pull HTML from the site, save to cache/. Idempotent."""

def parse() -> None:
    """Stage 2: read cache/*.html, produce data/players.json. Pure function from disk to disk."""

def load(db: DatabasePort) -> None:
    """Stage 3: read data/players.json, write to db via the port. Idempotent."""

def main(db: DatabasePort) -> None:
    fetch(); parse(); load(db)
```

In production you'll usually run all three. In development, you'll mostly run stage 2 and 3 over and over, occasionally re-running stage 1 when you want fresher data.

> **This whole thing is the scraper _service_** (`services/scraper/`, see [doc 02](02-monorepo-and-tooling.md)). It's a standalone program: it runs, fills the database, and exits. Stage 3 — `db.save_players(...)` — is its _only_ point of contact with the rest of the system. The backend never imports the scraper and never calls it; the two meet at the database. That single `db` argument threaded through `load()` and `main()` is the seam, and [doc 04](04-ports-and-adapters.md#but-where-does-the-argument-actually-come-from) shows exactly where it gets constructed.

## Typing the scraped data

Stage 2 is the trust boundary. HTML goes in (we don't trust it). Typed objects come out (we trust them, because we just checked). This is where Pydantic earns its keep (see [doc 03](03-typed-python.md)).

```python
from pydantic import BaseModel, Field

class ScrapedPlayer(BaseModel):
    """The shape of a player as it comes out of the parser."""
    id: str
    name: str = Field(min_length=1)
    team: str
    position: str
    goals: int = Field(ge=0)
    matches_played: int = Field(ge=0)
```

If a page is broken or missing fields, `ScrapedPlayer.model_validate(...)` raises `ValidationError` with a useful message. You catch that and decide what to do — log it, skip the row, fail the run, etc. **You do not silently fall back to default values.** A `0` you made up looks identical to a real `0` once it's in the database.

Once past validation, convert to the internal `Player` dataclass (the one from [doc 04](04-ports-and-adapters.md)) before handing off to stage 3.

## Idempotency

A run is **idempotent** if running it twice has the same effect as running it once. For our pipeline:

- **Stage 1 (fetch):** writes to `cache/<page>.html`. Re-running overwrites. Idempotent.
- **Stage 2 (parse):** writes to `data/players.json`. Re-running overwrites. Idempotent.
- **Stage 3 (load):** must use `INSERT OR REPLACE` (the `save_players` adapter does this) so two runs don't double-insert. Idempotent.

If you ever find yourself writing `INSERT INTO players ...` without an upsert, **you've broken idempotency**. Same data in → different DB state on second run is a bug, not a feature.

## Error handling, by layer

The temptation when scraping is to wrap everything in `try: ... except: pass` so the script "always finishes." Resist. The point of error handling is to **make the right thing happen at the right layer**, not to swallow errors silently.

| Layer | What can fail | How to handle |
|---|---|---|
| HTTP fetch | Network down, 404, 500, redirect, timeout | Retry with backoff (e.g. 3 attempts), then fail loudly. Log the URL. |
| HTML parse | Element missing, layout changed | Raise — this means the site changed and the scraper is now wrong. |
| Pydantic validation | Field out of expected range | Log, skip the row, continue. Track the count of skipped rows. |
| DB load | DB locked, schema mismatch | Fail loudly. This shouldn't happen in normal operation. |

Two principles cut across all of them:

1. **Distinguish "expected-rare" from "should-not-happen."** A missing player record on a known-broken page is expected-rare → log and skip. A schema mismatch is should-not-happen → fail loudly and stop.
2. **Never `except Exception: pass`.** If you genuinely want to ignore something, catch the specific exception type, and add a comment explaining why it's safe.

## Being a good citizen

You are about to point a script at someone else's website. A few baseline manners:

- **Rate limit yourself.** `time.sleep(0.5)` between page fetches at a minimum. This is a low-traffic site for a local league, not Wikipedia — don't hammer it.
- **Identify yourself.** Set a real `User-Agent` header like `fantasy-futsal-scraper/0.1 (school project)`. Don't pretend to be a browser if you're not.
- **Cache aggressively.** Stage 1's whole point is "don't re-fetch what you already have." If you're iterating on the parser, you shouldn't be making any HTTP requests at all.
- **Read the site's `robots.txt`.** It might restrict scraping certain paths. Respect it.

The site does not exist to host us. It exists to serve futsal fans. Pretend the league president is watching your traffic — because they could be.

## Common pitfalls

### "It worked when I ran it manually"

You ran it once, against a freshly-loaded cache, in a quiet network environment. The site went down for 30 seconds last Tuesday and your script crashed at 3am. The five edge cases your manual run didn't hit will surface in production.

**Fix:** Write the failure cases as tests (with a saved HTML fixture, no network), not just the happy path. Ticket #25 ("Add tests for scraper") is where this happens.

### Parsing with regex

HTML is not a regular language. Regex parsing of HTML works for the first three pages and breaks on the fourth because someone has a `<` in their name or a comment with `<table>` inside it. Use a real HTML parser (`BeautifulSoup`, `selectolax`, or `lxml`).

### Hardcoded selectors everywhere

If your `parse_player_table()` function has the CSS selector `"table.players > tbody > tr:nth-child(2) > td.name"` hardcoded six times, then when the site changes you have six places to fix and you'll miss one. Pull selectors out into named constants at the top of the parser module:

```python
SEL_PLAYER_NAME = "td.player-name"
SEL_PLAYER_GOALS = "td.player-goals"
```

The selectors are still going to break eventually. At least they break in one obvious place.

### Trusting the order of things

"The third `<td>` is always the team name" — until the site adds a column. Find elements by class/id/data attribute, not by position.

## Tickets this prepares you for

- **#15 — Research futsalvplzni.cz structure and identify data sources** (your first ticket — output a written summary of where the data lives, what selectors you'll need, and what gotchas the site has)
- **#17 — Create web scraper for player data** (yours — apply the three-stage pipeline pattern; do not write a one-function scraper)
- **#21 — Wire scraper to database adapter** (stage 3; uses the port, not SQLite directly)
- **#25 — Add tests for scraper** (parse-stage tests using saved HTML fixtures)
