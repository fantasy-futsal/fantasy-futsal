# 09 — Quality Gates

> Read after your first pre-commit hook failure (it will happen).

## The mental model

A "quality gate" is a robot that reads your code and complains so a human doesn't have to. In this project there are several, running at three different moments:

```
   ┌────────────┐     ┌──────────────┐     ┌──────────────────┐
   │  Editor    │ ──→ │  Pre-commit  │ ──→ │  CI (on PR)      │
   │  (live)    │     │  (lefthook)  │     │  (GitHub Actions)│
   └────────────┘     └──────────────┘     └──────────────────┘
   instant            ~1s on save         ~1min on push
   1st line of        2nd line of         3rd line of
   defense            defense             defense
```

Each layer catches the things the previous layer missed, and each is more expensive than the one before. The earliest layer that catches an issue is the cheapest. **The robots are not the enemy.** They are doing for free what a code reviewer would otherwise have to do tediously by hand.

## The robots

| Robot | Watches | What it catches |
|---|---|---|
| **ruff** | Python | Style, common bug patterns, unused imports, unused variables |
| **mypy --strict** | Python | Type mismatches, missing annotations, `None` not handled |
| **ESLint** | TypeScript/JS | Style, common bug patterns, unused vars |
| **Prettier** | TS/JS/JSON/Markdown/YAML | Formatting only — indentation, quotes, trailing commas |
| **svelte-check / tsc** | Svelte + TS | Type errors in Svelte components and TS files |
| **commitlint** | Commit messages | Conventional Commits format |
| **lefthook** | git events | Runs the above at the right moments |

### ruff

A fast Python linter that catches things like:

- `import os` that you never use
- A variable named `l` (easy to confuse with `1`)
- `except Exception as e:` followed by code that never uses `e`
- Inconsistent quote styles, weird whitespace

Run it with `pnpm lint` (which dispatches to the Python lint command under the hood). Most things ruff catches it can also _fix_: `ruff check --fix`. Get in the habit of running this before pushing.

### mypy --strict

The type checker, running in strict mode. Strict mode adds rules that make the checker more demanding — see [doc 03 — Typed Python](03-typed-python.md) for the full list. The summary:

- Every function must be fully annotated.
- `Any` doesn't silently leak through.
- `T | None` must be checked before use.

If mypy complains, **the fix is almost always in your code, not in mypy's config**. The temptation to add `# type: ignore` is real and almost always wrong. Use `# type: ignore[specific-error-code]` only when you genuinely know better than the checker and add a comment explaining why.

### ESLint + Prettier

For the TypeScript side. They split labor:

- **ESLint** = "this code might have a bug or violates a rule" (e.g. unused variable, `any` type).
- **Prettier** = "this code is formatted wrong" (e.g. tabs vs spaces, line length, quote style).

These two used to fight a lot; this project's config has them coexisting. You almost never need to think about Prettier — `pnpm format` rewrites your files to match. ESLint has rules you'll occasionally have to address by hand (e.g. "don't use `any`").

### svelte-check

The Svelte equivalent of `tsc --noEmit`. It type-checks your `.svelte` files, including props, slots, and the bits of TypeScript inside `<script>` blocks. Run it with `pnpm check`.

### commitlint

Runs on every `git commit` to validate your commit message. See [doc 08 — Git and PR workflow](08-git-and-pr-workflow.md).

### lefthook

The orchestrator. The config in `lefthook.yml` says, for example:

```yaml
pre-commit:
  parallel: true
  commands:
    lint:
      glob: '*.{js,ts,svelte,json}'
      run: pnpm exec eslint --fix {staged_files}
    format:
      glob: '*.{js,ts,svelte,json,md,yml,yaml}'
      run: pnpm exec prettier --write {staged_files}
```

This means: before every commit, on the JS/TS/Svelte/JSON files you're about to commit, run ESLint with auto-fix and Prettier. Other languages (Python, etc.) have their own pre-commit blocks added the same way.

The hooks `lefthook install` puts in place are local to your clone. **They won't be active until you run that command once.** First-time setup will be in the M0 instructions.

## When does each one run?

| Layer | Tool | What it does |
|---|---|---|
| Editor | (your editor's plugins) | Squiggly underlines as you type. Optional but recommended. |
| Pre-commit (lefthook) | ruff, ESLint, Prettier on staged files | Catches issues in what you're about to commit, ~1s. |
| Commit-msg (lefthook) | commitlint | Validates the message format, ~0.5s. |
| CI (GitHub Actions) | All of the above, on the whole codebase | Last line of defense before merge. ~1min. |

The pre-commit hook only checks files you _staged_, so it's fast. CI checks _everything_, so it can catch cases where you broke a file you didn't touch (e.g. by removing an import elsewhere).

## When a check fails

The most common reactions, ranked best to worst:

1. **Read the error message, fix the code.** The error almost always tells you exactly what's wrong. ✓
2. **Run the auto-fix.** `ruff check --fix`, `pnpm format`, etc. Often the fix is a one-liner that the tool can do for you. ✓
3. **Ask the mentor.** If the message is genuinely confusing, copy it into the next session. ✓
4. ~~Suppress the rule.~~ `# noqa`, `# type: ignore`, `// eslint-disable-line` — these turn off the robot for one line. Use only when you've understood the rule and disagree _with reason_. Add a comment explaining the reason.
5. ~~Disable the check globally.~~ Changing `ruff.toml` or `mypy.ini` to make your error go away. **Don't.** The config was set deliberately; changing it requires discussion.
6. ~~Bypass the hook.~~ `git commit --no-verify`, `git push --no-verify`. This pushes the cost to CI (or to the human reviewer). The robot catches it next time anyway, but now everyone else is also blocked.

## Why strict settings, on a small project

A reasonable question: "Isn't `mypy --strict` overkill for a school project? Why not start loose and tighten later?"

The honest answer: it's easier to start strict and stay strict than to start loose and try to tighten later. Once a codebase has 200 untyped functions, the cost of typing them all retroactively is large enough that nobody ever does it. The discipline costs almost nothing when added one file at a time as the file is written.

This is also a learning project. The robots being picky is _the point_. Each rejected commit is a tiny lesson in a specific kind of code smell. By the end of the MVP, the rules that felt arbitrary will feel obvious — that's the curriculum doing its job.

## What to install in your editor (optional but useful)

Squiggly underlines while you type are much faster feedback than `pnpm lint`. If you use VS Code:

- **Python:** the official Python extension (handles ruff + mypy via the language server).
- **Svelte:** the official Svelte extension (gives you `svelte-check` errors live).
- **ESLint + Prettier:** the corresponding extensions, set to "format on save."

If you use a different editor, the same tools are usually available — search "<editor> ruff" / "<editor> svelte" / etc.

## Tickets this prepares you for

- All of them, indirectly — the robots run on every PR.
- **#5 — Configure Python linting (ruff + mypy --strict)** (mentor task; this is the config that makes the above real)
- **#4 — Configure TypeScript linting (ESLint + Prettier + TS strict)** (mentor task; same on the TS side)
- **#7 — Setup lefthook for git hooks** (mentor task; the orchestrator config)
- **#6 — Configure commitlint with conventional-commits** (mentor task; the commit-message rule)
