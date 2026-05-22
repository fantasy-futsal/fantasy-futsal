# 08 — Git and PR Workflow

> Read before your very first PR.

## The short version

1. Make a branch: `git switch -c feat/scraper-research`
2. Commit using **Conventional Commits**: `feat: add stage-1 fetch for player pages`
3. Push: `git push -u origin feat/scraper-research`
4. Open a PR. The mentor reviews. Address feedback by pushing more commits.
5. When approved, the PR is **squash-merged** to `master`. Your branch is deleted.
6. Pull `master`, delete your local branch, start over for the next ticket.

The rest of this doc explains _why_ each step looks the way it does.

## Why commit messages matter

A future you (or someone else) opens `git log` and sees:

```
abc1234 fixed it
def5678 wip
ghi9012 stuff
jkl3456 more changes
```

That history is useless. It tells you _that_ things changed, not _what_ or _why_. Now compare:

```
abc1234 fix(scraper): handle missing team field on goalkeeper pages
def5678 feat(scraper): add retry with backoff on HTTP 5xx
ghi9012 refactor(database): extract row-to-Player conversion to helper
jkl3456 feat(api): paginate GET /players via limit/offset
```

Same number of commits. Now `git log` is a changelog. You can search it (`git log --grep=scraper`), generate release notes from it, and use `git blame` meaningfully. The first version of the project where this matters is the version _after_ you've stopped caring about commit messages — by then, it's too late.

## Conventional Commits — the format

```
<type>(<scope>): <short summary>

<longer body, optional>

<footer, optional>
```

The first line is mandatory. The rest is optional but encouraged for non-trivial changes.

### Types

| Type | When to use |
|---|---|
| `feat` | New user-facing feature or capability |
| `fix` | Bug fix |
| `refactor` | Code change that doesn't add a feature or fix a bug |
| `docs` | Documentation only (this doc you're reading was added with `docs:`) |
| `test` | Adding or improving tests |
| `chore` | Tooling, build scripts, dependency bumps |
| `ci` | CI configuration only |
| `style` | Formatting only (rare — usually a robot did it, not you) |
| `perf` | Performance improvement |
| `build` | Build system or external dependencies |

If you can't decide between two, pick the one that best describes the _purpose_ of the change for a reader of the changelog. A change that adds tests _and_ a feature is a `feat` (with tests; the tests aren't the point).

### Scope

The optional `(scope)` says which area of the codebase the change touched. We've been using `scraper`, `api`, `database`, `frontend`, `infra`. Keep it short and consistent. Look at recent commits with `git log --oneline -20` to see what scopes are already in use before inventing a new one.

### The short summary

- Imperative mood. "add scraper" not "added scraper" or "adds scraper."
- Lowercase. Don't capitalize "Add scraper."
- No trailing period.
- Under ~70 characters total.

### Examples from this project's style

```
feat(scraper): add stage-1 fetch for player pages
fix(database): handle empty position string in SQLite adapter
docs: add teaching docs for ports and adapters
chore: bump prettier to 3.8.3
test(scraper): cover redirect handling in fetch stage
```

## Why feature branches + rebase + squash-merge

Three Git policies, working together to keep `master` clean.

### Feature branches

`master` is a release-ready branch. You don't commit to it directly. Every change goes through a branch. The branch name should match the work: `feat/scraper-research`, `fix/null-positions`, `docs/teaching-folder`.

This isolates work-in-progress (`master` never sees a half-broken commit) and makes PRs reviewable as units.

### Rebase, not merge, to stay current

While you're working on your branch, `master` may move (mentor lands other PRs). To pull in those changes, you **rebase**, not merge:

```bash
git fetch origin
git rebase origin/master
```

What `rebase` does: replays your branch's commits on top of the new `master`. Result: your branch looks like it was always built on top of the latest code. No `Merge branch 'master' into ...` commits cluttering the log.

If rebase produces conflicts, you resolve them on each commit as Git stops, then `git rebase --continue`. The first time this happens you'll want to walk through it with the mentor — the second time you'll know what you're doing.

### Squash-merge to `master`

When the PR is approved, GitHub squash-merges it: your N commits on the branch become **one** commit on `master`, with a polished message. That single commit:

- Is the unit of "this feature shipped on this date."
- Can be reverted as a unit if it breaks something.
- Keeps `master`'s log scanable — one line per shipped feature, not per work-in-progress save.

The work-in-progress commits on your branch don't have to be perfect — they get squashed away. The **PR title** is what becomes the squashed commit message, so the PR title should follow Conventional Commits format.

This combination — feature branches + rebase + squash — gives `master` a **linear history**: every commit on `master` is a complete, named change, in order. `git log master --oneline` reads like a changelog because it _is_ one.

## Lefthook will catch your commit messages

This project uses [lefthook](https://lefthook.dev) to run checks before each commit.

> **One-time setup:** the hooks don't activate until you run `pnpm exec lefthook install` once, right after cloning. Until you do, commits skip every check below — which feels fine right up until CI rejects your PR for something the hook would have caught locally. Do it as part of first-time setup; the full checklist is in [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

The hook most relevant to you here:

```yaml
# lefthook.yml (excerpt)
commit-msg:
  commands:
    commitlint:
      run: pnpm exec commitlint --edit {msg_file}
```

When you run `git commit`, lefthook fires `commitlint`, which validates your commit message against the Conventional Commits rules above. If it doesn't match, the commit is **rejected**, and you get an explanation of what failed.

**Do not use `git commit --no-verify` to bypass this.** That flag exists for emergencies (the hook itself is broken in some edge case). Skipping the hook to push through a non-conventional message is exactly the kind of small shortcut that, repeated over a project's life, produces the useless `git log` from the top of this doc.

If the hook is genuinely wrong about your message (very rare), bring it up — that's a `chore(infra)` to fix the config.

## The PR cycle, step by step

A complete walkthrough of one ticket:

```bash
# 1. Start fresh from master
git switch master
git pull origin master

# 2. Make a branch for your ticket
git switch -c feat/scraper-research

# 3. Do the work. Commit as you go — these commits will be squashed.
#    Use real conventional commit messages anyway; they help review.
git add docs/research/futsalvplzni.md
git commit -m "feat(scraper): document data sources from futsalvplzni.cz"

# (... maybe a few more commits ...)

# 4. Push to GitHub
git push -u origin feat/scraper-research

# 5. Open a PR (via the GitHub web UI or `gh pr create`).
#    The PR title is the commit message that will land on master, so:
#    "feat(scraper): research data sources on futsalvplzni.cz"
#    The PR body should reference the ticket: "Closes #15"

# 6. Mentor reviews. You address comments by pushing more commits to the branch.

# 7. If master moved while the PR sat:
git fetch origin
git rebase origin/master
git push --force-with-lease

# 8. PR approved → mentor squash-merges → your single commit lands on master.

# 9. Clean up
git switch master
git pull origin master
git branch -D feat/scraper-research
```

## Common pitfalls

### Committing to `master` directly

`master` is meant to be protected against direct commits via branch protection rules. If you somehow manage to commit there, the fix is `git reset HEAD~1` (before pushing) — but the more important thing is to develop the habit of always making a branch first. Treat `master` as read-only on your machine.

### `git push --force` to a branch other people care about

`--force` rewrites history on the remote. If anyone else has pulled your branch, their copy is now out of sync, and they get a nasty merge mess. The safer flag is `--force-with-lease`: it forces _only if_ your local view of the remote is up to date. **Always prefer `--force-with-lease` over `--force`**. On a personal feature branch nobody else uses, this distinction is theoretical — but the habit transfers to branches where it matters.

### Pushing WIP debugging code

`print("AAAAAA")`, `// TODO remove this`, commented-out blocks — these slip in when you're debugging and forget. Two preventions:

1. `git diff` before every `git add` to see what you're staging.
2. `git diff --cached` before `git commit` to see what you're committing.

Treat both as a 30-second self-review step.

### `git push --no-verify`

Skips pre-push hooks. Same reasoning as `--no-verify` on commit: the hooks exist to catch things you'd rather catch now than in CI. If a hook is wrong, fix the hook.

### Long-lived branches

A branch that lives for two weeks while `master` moves a lot ahead becomes a rebase nightmare. **Aim to merge branches within a few days.** If a task is bigger than that, split it: land a "scaffolding" PR first, then build on top.

## Tickets this prepares you for

All of them — this doc is for every PR you'll ever open in this repo. Re-read after your first failed commit-msg hook; it'll click harder then.
