# ADR-0001: Selected languages and frameworks

## Status

Accepted.

## Context

Fantasy Futsal is a small, end-to-end web product: it scrapes player statistics
from [futsalvplzni.cz](https://futsalvplzni.cz), stores them, serves them over an
HTTP API, and renders them in a browser (see
[doc 01 — The big picture](../teaching/01-the-big-picture.md)). That shape spans
two natural halves:

- A **browser frontend** — pages, interactivity, eventually fantasy-team
  building and leaderboards.
- A **server side** — HTML scraping, data modelling, an HTTP API.

This is also a teaching project. The chosen stack has to be _learnable_ by
someone who knows Python and HTML/CSS at a working level, with good
documentation and a healthy ecosystem, while still resembling how real systems
are built.

## Decision

**Frontend: TypeScript with SvelteKit and Tailwind CSS.**

- **TypeScript** over plain JavaScript so the type checker is a quality gate
  from the start (see [ADR-0003](0003-linting-and-formatting.md)).
- **SvelteKit** (Svelte 5) as the application framework. Its compiler-based
  model means little runtime boilerplate, the component syntax is close to plain
  HTML/CSS/JS, and routing, data loading, and builds come in one coherent
  package via Vite.
- **Tailwind CSS** for styling — utility classes keep styling co-located with
  markup and avoid a separate bikeshed about CSS architecture on a small UI.

**Server side: Python with FastAPI.**

- **Python** is the language the student already knows, and it is the natural fit
  for the scraping and data work at the heart of the MVP.
- **FastAPI** for the HTTP API: type-hint-driven request/response models,
  automatic OpenAPI docs, and async support, all built on standards (ASGI,
  Pydantic) that reward the typed-Python discipline this project already enforces.

The scraper is also Python, sharing models with the backend, but it is a
**standalone service**, not part of the API — that boundary is recorded in
[ADR-0002](0002-monorepo-structure.md).

## Consequences

**Positive**

- One typed language per side (TypeScript, typed Python) makes the strict
  type-checking story in [ADR-0003](0003-linting-and-formatting.md) uniform.
- FastAPI's Pydantic models and SvelteKit's TS types give a clear, typed contract
  at the HTTP boundary; shared TS API types live in `libs/ts`.
- Both frameworks have first-class docs and large communities — good for a
  learner who will be reading reference material constantly.
- Python keeps the scraper, models, and API in one language, so shared code
  (e.g. the `Player` dataclass) lives in one place.

**Negative / trade-offs**

- Two languages mean two toolchains (`pnpm` + `uv`), two linters, two type
  checkers. [ADR-0002](0002-monorepo-structure.md) and
  [ADR-0003](0003-linting-and-formatting.md) absorb this cost deliberately.
- SvelteKit is less ubiquitous than React; fewer Stack Overflow answers, though
  its smaller surface area is easier to learn fully.
- Tailwind's utility-class markup looks noisy at first and is an acquired taste.

**Alternatives considered**

- _React/Next.js frontend_ — larger ecosystem, but more boilerplate and concepts
  to learn for a single-developer learning project; Svelte's simpler model won.
- _Node/Express backend_ — would unify on one language, but throws away Python's
  scraping/data strengths and the student's existing Python fluency.
- _Django backend_ — batteries-included, but heavier than needed for a thin
  read-mostly JSON API, and weaker on the typed-async story FastAPI gives.

## References

- [doc 01 — The big picture](../teaching/01-the-big-picture.md) — the end-to-end
  data pipeline these frameworks implement.
- [doc 06 — REST API with FastAPI](../teaching/06-rest-api-with-fastapi.md)
- [doc 07 — Frontend data flow](../teaching/07-frontend-data-flow.md)
- [ADR-0002](0002-monorepo-structure.md), [ADR-0003](0003-linting-and-formatting.md)
