# Architecture Decision Records

An **Architecture Decision Record** (ADR) is a short document that captures one
significant decision: the context that forced a choice, the option we picked,
and the consequences we accepted by picking it. The point is not ceremony — it's
that six months from now, when someone asks "why is the scraper a separate
service?" or "why `mypy --strict` on a school project?", the answer is written
down instead of living only in someone's head.

These differ from the [teaching docs](../teaching/README.md): teaching docs
explain _how the project works_ so you can build on it; ADRs explain _why it was
built that way_ so you can change it responsibly. If you find yourself
disagreeing with a decision here, that's allowed — but read the **Consequences**
first. The record exists so you argue against the actual trade-off, not a
strawman.

## Format

Every record follows the same shape:

- **Status** — `Accepted`, `Superseded by ADR-NNNN`, or `Deprecated`.
- **Context** — the forces at play; what made a decision necessary.
- **Decision** — what we chose, stated plainly.
- **Consequences** — what we gain and what we give up. Honest about both.
- **References** — links to the teaching docs and sibling ADRs.

An ADR is immutable once accepted. We don't edit a decision we changed our mind
about — we write a new ADR that supersedes it, so the history of the project's
thinking stays intact.

## The records

| #                                                 | Title                                | Decision in one line                                                                     |
| ------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------- |
| [0001](0001-selected-languages-and-frameworks.md) | Selected languages and frameworks    | TypeScript + SvelteKit + Tailwind on the frontend; Python + FastAPI on the backend.      |
| [0002](0002-monorepo-structure.md)                | Monorepo structure                   | One repo, two workspaces (pnpm + uv), an `apps` / `services` / `libs` layout.            |
| [0003](0003-linting-and-formatting.md)            | Linting and formatting               | ruff + `mypy --strict`, ESLint + Prettier + TS strict, commitlint — strict from day one. |
| [0004](0004-git-hooks-and-cicd.md)                | Git hooks and the quality-gate model | lefthook locally, GitHub Actions in CI, mirroring each other across three layers.        |
| [0005](0005-cicd-strategy.md)                     | CI/CD strategy                       | What runs on push/PR, plus feature-branch → rebase → squash-merge for a linear `master`. |
