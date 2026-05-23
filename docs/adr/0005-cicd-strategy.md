# ADR-0005: CI/CD strategy

## Status

Accepted.

## Context

[ADR-0004](0004-git-hooks-and-cicd.md) establishes that CI is the enforced,
authoritative layer of the quality-gate model and that it mirrors the local
hooks. This ADR pins down the rest of the continuous-integration story: which
jobs run, on which Git events, and the branching and merge policy that keeps the
`master` history meaningful.

`master` is meant to be release-ready and protected against direct commits. For
that to hold, every change must pass through a reviewed, checked path, and the
history of `master` should read like a changelog rather than a stream of
work-in-progress saves.

## Decision

**Run the full check suite in GitHub Actions on push and pull request, and
integrate changes via feature branch → rebase → squash-merge.**

### What CI runs

The same tools as the local hooks ([ADR-0003](0003-linting-and-formatting.md)),
but across the whole codebase rather than only staged files:

- **Linting** — ruff (Python), ESLint (TS/Svelte).
- **Formatting check** — Prettier in `--check` mode (fails on unformatted files;
  it does not rewrite in CI).
- **Type checks** — `mypy --strict` (Python), `tsc` / svelte-check (TS/Svelte).
- **Commit message** — Conventional Commits format.

CI installs both toolchains it needs: Node (pinned by `.nvmrc`) with `pnpm`, and
Python (**pinned to 3.14**) with `uv`.

### On which events

- **On pull request** — the gate that blocks merging. A PR cannot be merged with
  a red check.
- **On push** — runs on branch pushes too, so contributors get a signal without
  waiting for a PR.

### Branching and merge policy

- **Feature branches.** No direct commits to `master`. Each change lives on a
  branch named for its work (`feat/...`, `fix/...`, `docs/...`).
- **Rebase to stay current.** When `master` moves under a branch, the branch is
  rebased (`git fetch && git rebase origin/master`), not merged — no
  `Merge branch 'master'` noise. Force-pushes use `--force-with-lease`.
- **Squash-merge to `master`.** An approved PR's commits collapse into a single
  commit whose message is the PR title (so the PR title follows Conventional
  Commits). That commit is the unit of "this shipped" and the unit of revert.

Together these give `master` a **linear history**: one complete, named change per
commit, in order — a log that reads as a changelog because it is one.

This is CI (continuous integration). Continuous _deployment_ is intentionally out
of scope for the foundation milestone; deployment targets will be decided in a
later ADR when the app is closer to running somewhere.

## Consequences

**Positive**

- Nothing reaches `master` without passing the same checks every contributor
  runs locally — no "works on my machine" merges.
- `git log master --oneline` is a clean, scannable changelog; any feature can be
  reverted as one commit.
- Rebase + squash keeps the graph free of merge-commit clutter, so `git blame`
  and `git bisect` stay meaningful.
- Running on push (not only PR) shortens the feedback loop.

**Negative / trade-offs**

- Squash-merge discards the granular work-in-progress commits on a branch —
  accepted, since those commits are saves, not history worth keeping.
- Rebasing rewrites branch history and needs `--force-with-lease`; the first
  conflict resolution has a learning curve.
- Long-lived branches drift far from `master` and become painful to rebase, so
  the policy is to merge within a few days and split larger work.
- CI parity with the local hooks must be maintained by hand
  ([ADR-0004](0004-git-hooks-and-cicd.md)).

**Alternatives considered**

- _Merge commits instead of squash_ — preserves every commit but litters
  `master` with WIP and merge nodes; rejected for readability.
- _Trunk-based direct commits_ — too little safety for a learning repo where
  `master` should always be green.

## References

- [doc 08 — Git and PR workflow](../teaching/08-git-and-pr-workflow.md) — the
  branch/rebase/squash cycle step by step.
- [doc 09 — Quality gates](../teaching/09-quality-gates.md) — CI as the third
  layer of defence.
- [ADR-0004](0004-git-hooks-and-cicd.md) — local hooks that CI mirrors.
- [ADR-0003](0003-linting-and-formatting.md) — the checks CI enforces.
