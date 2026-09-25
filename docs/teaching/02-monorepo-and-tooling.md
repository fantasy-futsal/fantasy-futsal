# 02 — Monorepo and Tooling

> What you should know before opening your first PR — even a one-line one.

This describes the structure as it _should_ be once the M0 (Foundation) milestone is complete. If something described here doesn't exist on disk yet, that's a foundation ticket that hasn't been picked up — flag it to the mentor instead of trying to recreate it on your own.

## What a monorepo is

A "monorepo" is one Git repository that contains multiple related projects. Our repo holds:

- A **frontend** (SvelteKit + TypeScript)
- A **backend** (FastAPI + Python)
- A **scraper service** (standalone Python — see [doc 01](01-the-big-picture.md#the-scraper-is-a-separate-service))
- **Shared libraries** in both languages, used by the apps and the service

If you've only ever seen one-repo-per-project setups, the question is reasonable: why bother? The honest answer is "for a project this size it doesn't matter that much, but it makes a few things easier":

- **One PR can change frontend and backend together** when they're co-evolving (e.g. adding a new field to the player JSON).
- **Shared code has a home.** When the scraper and the API both need the same `Player` dataclass, it lives in `libs/python/database/` and gets imported from both places — not copied. This is exactly why the scraper-as-separate-service idea works without duplication.
- **One source of truth for tooling.** One `.prettierrc`, one `pyproject.toml` holding the Python tool config, one set of git hooks.

The cost is that you need workspace-aware package managers — which is what `pnpm` and `uv` are.

## The layout

```
fantasy-futsal/
├── apps/                       ← long-running, user-facing applications
│   ├── frontend/                  SvelteKit app — what users see
│   └── backend/                   FastAPI app — the HTTP API
├── services/                   ← standalone background processes, not user-facing
│   └── scraper/                   scrapes futsalvplzni.cz, writes to the DB, exits
├── libs/                       ← shared code, never deployed on its own
│   ├── ts/                        TypeScript libs (e.g. shared API types)
│   └── python/                    Python libs (e.g. database/, models/)
├── docs/
│   ├── teaching/                  you are here
│   └── adr/                       architecture decision records
├── .github/
│   └── workflows/                 GitHub Actions — CI
├── package.json                ← pnpm root
├── pnpm-workspace.yaml         ← tells pnpm which folders are packages
├── pyproject.toml              ← uv workspace root + Python tool config
│                                  ([tool.ruff] and [tool.mypy] live here, not in
│                                   separate ruff.toml / mypy.ini files)
├── eslint.config.js            ← TS linter config
├── .prettierrc                 ← TS/Markdown formatter config
├── lefthook.yml                ← git hooks
└── commitlint.config.js        ← commit message rules
```

The rule of thumb — there are three top-level homes for code, and the question to ask is "what kind of thing am I building?":

- **Something a _user_ interacts with, that stays running → `apps/`** (the frontend, the API)
- **A standalone process that does a job and exits, that no user talks to directly → `services/`** (the scraper)
- **Code that _other_ code imports, deployed by nobody on its own → `libs/`** (the database port, shared models)

The line between an app and a service is "does it serve users / stay up?" (app) versus "does it run a job and stop?" (service). If you genuinely can't decide, ask — but most things are obvious once you ask that question.

## Two workspaces, one repo

A "workspace" here means: a package manager that understands "this repo has multiple packages, please install dependencies and resolve imports across them sensibly."

### pnpm workspace (TypeScript)

`pnpm-workspace.yaml` lists the TS packages:

```yaml
packages:
  - 'apps/frontend'
  - 'libs/ts/*'
```

So when you run `pnpm install` at the repo root, pnpm installs deps for the frontend _and_ any `libs/ts/*` packages, and it sets things up so `import ... from '@fantasy-futsal/some-lib'` works inside the frontend without any path-manipulation hacks.

### uv workspace (Python)

`pyproject.toml` at the root declares a uv workspace listing the Python packages (the backend app, the scraper service, and each `libs/python/*` library). After `uv sync`, the imports work the way they should — and crucially, the backend _and_ the scraper can both import the same shared library:

```python
# inside apps/backend/backend/app.py
from libs.python.database.port import DatabasePort, Player

# inside services/scraper/__main__.py — same import, different process
from libs.python.database.port import DatabasePort, Player
```

**Important: do not use `sys.path.append(...)` or set `PYTHONPATH` to make imports work.** If an import fails, the right fix is "this package needs to be declared in the workspace and installed properly," not "trick Python into looking somewhere extra." If you ever feel the urge to reach for `sys.path`, stop and ask — there is a proper fix.

## Common commands

Run all of these from the **repo root** unless noted:

| What you want | Command |
|---|---|
| Install all JS deps | `pnpm install` |
| Install all Python deps | `uv sync` |
| Start the frontend dev server | `pnpm dev` |
| Start the backend server | `uv run python -m backend` |
| Run the scraper once | `uv run python -m scraper` |
| Run all linters | `pnpm lint` |
| Auto-format everything | `pnpm format` |
| Run all type checks | `pnpm check` |
| Run all tests | `pnpm test` |

A few of these (notably the backend ones) only work after the corresponding tickets are done. If a command's target file doesn't exist yet, that's a ticket waiting to be picked up.

## Where do I add my new code?

This question comes up on _every_ ticket. Some shortcuts:

- **A new HTTP route handler** → `apps/backend/`
- **Scraper logic, or a new standalone batch job** → `services/scraper/` (or a new `services/<name>/`)
- **A new page or component the user sees** → `apps/frontend/src/`
- **A data type or function used by _more than one_ thing** (e.g. by both the backend and the scraper) → `libs/python/<name>/` or `libs/ts/<name>/`
- **A reusable Svelte component used by multiple pages** → `apps/frontend/src/lib/` (this is SvelteKit's convention)

**Don't pre-emptively put things in `libs/`.** A piece of code only belongs in a library when at least two things actually import it. Premature libraries are a real source of mess — they grow stubs, untested branches, and APIs designed for hypothetical callers that never show up. Start where the code is used; move to `libs/` when a second caller appears. (The `database` library is the one place we _start_ shared, because we know from day one that both the scraper and the backend need it.)

## Tickets this prepares you for

- **#2 — Initialize pnpm workspace with SvelteKit** (mentor task, already done — this is _why_ you can run `pnpm dev` today)
- **#3 — Initialize uv workspace for Python** (mentor task — without this, the backend doesn't have a home yet)
- All `good first issue` tickets: every PR you open will touch this layout, so understand it before your first change.
