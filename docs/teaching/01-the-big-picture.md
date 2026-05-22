# 01 — The Big Picture

## What we are building

A **fantasy futsal** app for the Pilsen futsal league ([futsalvplzni.cz](https://futsalvplzni.cz)).

The same idea as fantasy football, but for the local futsal league:

1. Real players score real goals in real matches over the season.
2. We scrape those statistics from the league website.
3. Users on our app build a "fantasy team" by picking real players.
4. We award fantasy points based on what those players did in real life.
5. Users compete against each other in leagues and see leaderboards.

That's the whole product. Everything in the backlog is a step toward that picture.

## The data pipeline

The shape of the system, end-to-end, is a one-way flow:

```
                 (somewhere on the internet)
                  futsalvplzni.cz HTML pages
                              │
                              │  HTTP + HTML parsing
                              ▼
                       ┌──────────────┐
                       │   Scraper    │   services/scraper (Python)
                       │  (service)   │   issue #17 — a SEPARATE process
                       └──────┬───────┘
                              │  typed Player / Match / Stats objects
                              ▼
                    ┌────────────────────┐
                    │   DatabasePort     │   libs/python/database
                    │   (Protocol)       │   issue #18
                    └─────────┬──────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
        ┌───────────────┐           ┌───────────────┐
        │   SQLite      │           │  Firestore    │
        │   adapter     │           │  adapter      │
        │   (now)       │           │  (later)      │
        │   issue #19   │           │  issue #33    │
        └───────────────┘           └───────────────┘
                              │
                              │  query results
                              ▼
                       ┌──────────────┐
                       │   FastAPI    │   apps/backend
                       │   (Python)   │   issue #20
                       └──────┬───────┘
                              │  JSON over HTTP
                              ▼
                       ┌──────────────┐
                       │  SvelteKit   │   apps/frontend
                       │  + Tailwind  │   issues #23, #24
                       └──────────────┘
                              │
                              ▼
                       (browser, table of players)
```

Read it top to bottom. Data flows down. **The frontend never knows where the data came from** — it just talks to FastAPI. FastAPI never knows whether the database is SQLite or Firestore — it just talks to `DatabasePort`. Each layer only knows about the layer directly below it.

This is the single most important property of the design. It is why we can swap SQLite for Firestore later without rewriting the API, and why we could swap the scraper for a different data source without rewriting anything below it.

### The scraper is a separate service

Notice that the scraper is _not_ part of the backend. It's a standalone program that lives in `services/scraper/` and runs on its own — on a schedule, or by hand, whenever we want fresh data. This is deliberate, and it's worth understanding why, because it introduces a third kind of building block beyond "an app" and "a library":

- The **scraper** runs, writes player data into the database, and exits. It does not serve HTTP. Nobody calls it; it calls the database.
- The **backend** assumes the data is already in the database. It reads from the database to answer HTTP requests. It never calls the scraper, and it doesn't care _when_ the scraper last ran.

The two never talk to each other directly. There's no message queue, no broker, no "scraper, please refresh" endpoint. **The database is the single source of truth, and it's the only thing the two share.** The scraper writes; the backend reads; the database sits in the middle.

This is a small taste of a "microservices" style: independent processes with separate jobs that integrate through shared data rather than direct calls. For a project this size we could have put the scraper inside the backend — but keeping it separate makes the boundaries obvious and is closer to how real systems are built. You'll see exactly how the pieces get wired together in [doc 04 — Ports and adapters](04-ports-and-adapters.md).

## The five milestones

The backlog is organized into milestones on GitHub. Each one is a chunk of the picture above.

| | Milestone | What it unlocks |
|---|---|---|
| M0 | **Foundation** | Monorepo, linting, CI, ADRs. The plumbing — mostly done by the mentor. |
| M1 | **MVP: Data Pipeline** | The whole pipeline above, end to end. Scrape → store → API → table in the browser. **This is where you start.** |
| M2 | **Game Core** | Scoring rules, fantasy points calculation. Now the data _means_ something. |
| M3 | **User System** | Auth, profiles, "this team belongs to me." |
| M4 | **Competition** | Leagues, matchups, leaderboards. Users compete. |
| M5 | **Polish** | UI/UX, error handling, performance. |

By the end of M1 the app does not do anything _fun_ yet — it just shows a table of players. That's intentional. The point of M1 is to prove that the **pipeline works end-to-end** before we add game mechanics on top of it. If the pipeline is shaky, everything we build on it will be shaky.

## Who does what

The backlog uses two labels to split work:

- **`mentor task`** — infrastructure, decisions, architecture scaffolding. The mentor writes these so that you have a stable place to add code.
- **`good first issue`** — concrete, well-defined feature work with clear acceptance criteria. **These are yours.**

A few tickets in the middle (like "Define database port/interface" #18) are mentor tasks because the _interface_ is a teaching moment that needs explanation, but the _implementations_ (SQLite, Firestore) are yours.

You will see this pattern repeat: mentor lays the rails, you drive the train.

## What "done" looks like for the MVP

When you finish M1, you can:

1. Run a Python script and it scrapes futsalvplzni.cz into a local SQLite database.
2. Start the FastAPI server and `GET /players` returns the scraped data as JSON.
3. Start the SvelteKit dev server, open `localhost:5173`, and see a table of players in your browser.

That's it. No login. No fantasy points. No leagues. Just data flowing from a website you don't own, all the way to a table in a browser you control. That is the foundation everything else stands on.

## Tickets this prepares you for

This doc is orientation — it does not prepare you for any single ticket, it prepares you for **all of them**. Read it once, then move on to [02 — Monorepo and tooling](02-monorepo-and-tooling.md).
