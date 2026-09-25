# ADR-0003: Linting and formatting

## Status

Accepted.

## Context

Two languages ([ADR-0001](0001-selected-languages-and-frameworks.md)) in one repo
([ADR-0002](0002-monorepo-structure.md)) means two sets of style and correctness
rules to enforce. Without automated enforcement, a codebase drifts: mixed quote
styles, dead imports, untyped functions, `any` leaking through, inconsistent
commit messages. Each of those is cheap to prevent and expensive to clean up in
bulk later.

This is also a learning project, so the linters do double duty: every rejected
edit is a small, specific lesson in a kind of code smell.

## Decision

**Adopt strict linting, formatting, and type-checking on both sides, from day
one.**

Python (config in the root `pyproject.toml`, per
[ADR-0002](0002-monorepo-structure.md)):

- **ruff** — fast linter: unused imports/variables, bug-prone patterns, style.
  Most findings are auto-fixable with `ruff check --fix`.
- **mypy `--strict`** — every function fully annotated, no silent `Any`,
  `T | None` must be narrowed before use.

TypeScript / Svelte:

- **ESLint** (`eslint.config.js`, flat config) on top of the recommended JS and
  `typescript-eslint` rule sets; `@typescript-eslint/no-explicit-any` is on.
- **Prettier** (`.prettierrc`: tabs, single quotes, no trailing commas, width 100) for formatting only — `pnpm format` rewrites files to match.
- **TypeScript strict mode** and **svelte-check** for type errors in `.ts` and
  `.svelte` files.

Commits:

- **commitlint** (`commitlint.config.js`, extending
  `@commitlint/config-conventional`) enforces Conventional Commits.

The division of labour is deliberate: **Prettier owns formatting** (whitespace,
quotes, commas), **ESLint/ruff own correctness and smells** (unused vars, `any`,
bug patterns), **mypy/tsc/svelte-check own types**. They are configured to
coexist rather than fight (e.g. `eslint-config-prettier` disables ESLint's
stylistic rules).

These tools are _what_ runs. _When_ and _where_ they run — editor, pre-commit,
CI — is the subject of [ADR-0004](0004-git-hooks-and-cicd.md).

## Consequences

**Positive**

- Style debates are settled by config, not by review comments — reviewers spend
  their attention on logic.
- `mypy --strict` and TS strict catch a whole class of `None`/type bugs before
  runtime, which matters most across the typed HTTP and database boundaries.
- Conventional Commits make `git log` a readable changelog and enable squash
  messages and release notes (see [ADR-0005](0005-cicd-strategy.md)).
- Starting strict is cheap: typing one file as it's written costs almost nothing.

**Negative / trade-offs**

- Strict checks reject more edits, which feels like friction early on — accepted
  as the cost of not paying down debt later.
- Two linters and two type checkers are more config to maintain.
- The escape hatches (`# type: ignore`, `# noqa`, `eslint-disable`) exist but are
  policy-discouraged: use only with a specific error code and a comment
  explaining why. Loosening the shared config to silence an error is not allowed
  without discussion — the settings were chosen deliberately.

**Alternatives considered**

- _Start loose, tighten later_ — rejected: once a codebase has hundreds of
  untyped functions, nobody ever retrofits the annotations. Strict-from-day-one
  avoids the cliff.
- _Black instead of ruff's formatter / separate flake8 + isort_ — ruff
  consolidates linting (and formatting) into one fast tool, fewer moving parts.

## References

- [doc 09 — Quality gates](../teaching/09-quality-gates.md) — each robot, what it
  catches, and why strict on a small project.
- [doc 03 — Typed Python](../teaching/03-typed-python.md) — what `mypy --strict`
  demands.
- [doc 08 — Git and PR workflow](../teaching/08-git-and-pr-workflow.md) —
  Conventional Commits.
- [ADR-0004](0004-git-hooks-and-cicd.md) runs these tools at three layers.
