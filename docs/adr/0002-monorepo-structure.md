# ADR-0002: Monorepo structure

## Status

Accepted.

## Context

The project is made of several moving parts that evolve together: a SvelteKit
frontend, a FastAPI backend, a standalone scraper service, and shared code in
both TypeScript and Python (see
[ADR-0001](0001-selected-languages-and-frameworks.md)). These parts share
contracts — the frontend consumes the shape of the API's JSON; the scraper and
the backend both read and write the same `Player` model. We need a repository
layout that lets those contracts stay in sync without copy-paste, while still
keeping the boundaries between parts visible.

The two languages each come with a workspace-aware package manager (`pnpm` for
TypeScript, `uv` for Python) that can resolve imports across multiple packages in
one tree — which makes a single repository practical rather than painful.

## Decision

**Use a single monorepo with two workspaces and a three-home layout.**

```
fantasy-futsal/
├── apps/        long-running, user-facing applications (frontend, backend)
├── services/    standalone background jobs that run and exit (scraper)
├── libs/
│   ├── ts/      shared TypeScript packages (e.g. API types)
│   └── python/  shared Python packages (e.g. database/, models/)
├── docs/        teaching/ and adr/
└── .github/     CI workflows
```

The deciding question for where code lives is _"what kind of thing am I
building?"_:

- **A user interacts with it and it stays running → `apps/`**
- **It runs a job and exits, no user talks to it → `services/`**
- **Other code imports it, nobody deploys it alone → `libs/`**

Two workspaces sit at the root:

- **pnpm workspace** — `pnpm-workspace.yaml` lists `apps/frontend` and
  `libs/ts/*`. `pnpm install` at the root wires cross-package imports like
  `@fantasy-futsal/some-lib`.
- **uv workspace** — the root `pyproject.toml` declares the Python members (the
  backend app, the scraper service, each `libs/python/*`). `uv sync` makes
  `from libs.python.database.port import Player` resolve from both the backend
  and the scraper. `sys.path` hacks and `PYTHONPATH` tricks are forbidden — a
  failing import means a package needs declaring in the workspace, not tricking.

`libs/` is populated **reactively**: code moves there only when a second caller
appears. The one exception is the `database` library, shared from day one because
both the scraper and the backend provably need it.

## Consequences

**Positive**

- A single PR can change frontend and backend together when a contract changes
  (e.g. adding a field to the player JSON).
- Shared code has exactly one home; the scraper-as-separate-service design works
  with no duplication because both processes import the same `libs/python` code.
- One source of truth for tooling: one `.prettierrc`, one `pyproject.toml` for
  Python tool config, one `lefthook.yml`. This is what makes
  [ADR-0003](0003-linting-and-formatting.md) and
  [ADR-0004](0004-git-hooks-and-cicd.md) tractable.
- The `apps` / `services` / `libs` split keeps architectural boundaries legible
  at the directory level.

**Negative / trade-offs**

- Two package managers must both be installed and understood; onboarding has two
  install steps (`pnpm install`, `uv sync`).
- Workspace tooling is more machinery than a single-project repo needs at this
  size — accepted because it keeps the parts honest and mirrors real systems.
- A discipline risk: it's tempting to pre-emptively dump code in `libs/`.
  Premature libraries grow stubs and untested branches, so the rule is "two
  callers first."

**Alternatives considered**

- _One repo per project_ — would force shared models to be published as packages
  or copy-pasted, and split co-evolving changes across multiple PRs.
- _Flat layout (everything at the root)_ — loses the app/service/lib distinction
  that makes the scraper's "separate process" status obvious.

## References

- [doc 02 — Monorepo and tooling](../teaching/02-monorepo-and-tooling.md) — the
  layout and workspace commands in practice.
- [doc 01 — The big picture](../teaching/01-the-big-picture.md#the-scraper-is-a-separate-service)
  — why the scraper is a service, not part of the backend.
- [ADR-0001](0001-selected-languages-and-frameworks.md),
  [ADR-0003](0003-linting-and-formatting.md)
