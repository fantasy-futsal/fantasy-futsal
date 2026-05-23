# ADR-0004: Git hooks and the quality-gate model

## Status

Accepted.

## Context

[ADR-0003](0003-linting-and-formatting.md) decides _which_ checks run (ruff,
mypy, ESLint, Prettier, svelte-check, commitlint). This ADR decides _when_ they
run. A check is only useful if it runs reliably and as early as possible: the
earlier a problem is caught, the cheaper it is to fix. The worst outcome is a
check that exists but only fires after a human reviewer has already spent time on
the PR.

We also can't rely on every contributor running checks by hand — that's exactly
the kind of discipline that erodes under deadline pressure.

## Decision

**Run the checks at three layers, each catching what the previous one missed,
with local hooks and CI mirroring the same tools.**

```
   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐
   │  Editor  │ →  │  Pre-commit  │ →  │   CI (on PR/push) │
   │  (live)  │    │  (lefthook)  │    │  (GitHub Actions) │
   └──────────┘    └──────────────┘    └───────────────────┘
   instant         ~1s on staged       ~1min on whole repo
```

1. **Editor** — language-server squiggles as you type. Optional, fastest
   feedback, no enforcement.
2. **Pre-commit (lefthook)** — `lefthook.yml` runs the linters/formatters on
   **staged files only**, so it stays fast:
   - `pre-commit` runs ESLint `--fix` and Prettier `--write` on staged
     JS/TS/Svelte/JSON/Markdown/YAML (Python's ruff/mypy hook in the same way).
   - `commit-msg` runs commitlint against the message.
   - Hooks are local to a clone and **must be activated once** with
     `pnpm exec lefthook install` — documented in `CONTRIBUTING.md`.
3. **CI (GitHub Actions)** — runs the **same** tools across the **whole**
   codebase on push and PR. This is the enforced gate: it catches what the
   pre-commit hook can't (e.g. a file you didn't stage that you broke by removing
   an import elsewhere) and what a contributor skipped by not installing hooks.

The guiding principle: **local hooks and CI run the same checks.** Local hooks
are a courtesy that catches problems in ~1s; CI is the authority that catches
them regardless. Bypassing a hook (`git commit --no-verify`,
`git push --no-verify`) is not a way to ship a violation — CI rejects it anyway,
now having also blocked everyone else. The hooks are only bypassed if a hook
itself is broken, which is a `chore(infra)` fix to the config.

The specific CI events, jobs, and branch policy are detailed in
[ADR-0005](0005-cicd-strategy.md).

## Consequences

**Positive**

- Issues are caught at the cheapest layer that can catch them; CI is a backstop,
  not the first time a problem is seen.
- Local hooks auto-fix formatting on commit, so contributors rarely think about
  Prettier/ruff formatting at all.
- Because CI mirrors the hooks, "passes locally" reliably predicts "passes CI" —
  no surprise divergence between environments.
- lefthook is a single declarative config, language-agnostic, so adding a Python
  block sits next to the JS block in the same file.

**Negative / trade-offs**

- The hooks are inert until `lefthook install` is run — an easy first-time
  mistake. Mitigated by documenting it prominently in setup and by CI catching
  whatever the un-installed hook missed.
- Maintaining parity between the lefthook config and the CI workflow is manual:
  if a check is added in one place, it must be added in the other.
- A small duplication of intent (the same tools named in two files) is the price
  of defence-in-depth.

## References

- [doc 09 — Quality gates](../teaching/09-quality-gates.md) — the three-layer
  model and the `--no-verify` discussion.
- [doc 08 — Git and PR workflow](../teaching/08-git-and-pr-workflow.md) — where
  the commit-msg hook fits the PR cycle.
- [ADR-0003](0003-linting-and-formatting.md) — the checks these layers run.
- [ADR-0005](0005-cicd-strategy.md) — the CI side in detail.
