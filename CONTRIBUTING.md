# Contributing

This guide gets your machine set up to work on Fantasy Futsal. Do this once, before your first commit. If you're new to the project, also read [`docs/teaching/`](docs/teaching/README.md) to understand _what_ you're building before you start changing it.

> Some steps below depend on M0 (Foundation) tickets being complete — e.g. the uv workspace (#3) and lefthook setup (#7). If a command fails because a tool or config isn't wired up yet, that's a foundation ticket, not your machine. Flag it to the mentor.

## Required tools

| Tool | Version | What it's for |
|------|---------|---------------|
| **Node.js** | 24 (see [`.nvmrc`](.nvmrc)) | Runs the frontend toolchain; ships with `npm` |
| **pnpm** | 11+ | The JavaScript package manager we actually use (not `npm`) |
| **uv** | latest | Python package manager **and** Python version manager |
| **Python** | as pinned by the project | The backend, the scraper, and the shared Python libs |
| **Git** | any recent | Version control |

You do not install Python from python.org — `uv` installs and manages it for you. You do not install pnpm by hand if you use Corepack (it ships with Node). Details below.

## Install the tools

### macOS / Linux

```bash
# 1. nvm — manages Node versions. (https://github.com/nvm-sh/nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# then restart your shell, or `source ~/.nvmrc`-loading lines it added to your profile

# 2. Node 24 (the repo's .nvmrc pins this; `nvm install` reads it)
nvm install        # installs the version in .nvmrc
nvm use            # switches to it (run this whenever you enter the repo)

# 3. pnpm — easiest path is Corepack, which comes with Node
corepack enable pnpm
# (fallback if Corepack isn't available: `npm install -g pnpm`)

# 4. uv — Python package + version manager (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh
# restart your shell so `uv` is on PATH
```

### Windows

You have two options. **WSL2 is strongly recommended** — it gives you a real Linux environment, the tooling "just works," and you follow the macOS/Linux steps above verbatim. Native Windows works too, but expect a few more rough edges.

**Option A — WSL2 (recommended)**

```powershell
# In an elevated PowerShell:
wsl --install
# Reboot, let Ubuntu finish setting up, then open the Ubuntu terminal
# and follow the macOS / Linux instructions above inside it.
```

Keep the repo _inside_ the Linux filesystem (e.g. `~/code/fantasy-futsal`), not on the Windows `/mnt/c/...` mount — it's much faster and avoids line-ending surprises.

**Option B — native Windows (PowerShell)**

```powershell
# 1. nvm for Windows — NOTE: this is a different project from Unix nvm.
#    Install from https://github.com/coreybutler/nvm-windows/releases
#    It does NOT auto-read .nvmrc, so pass the version explicitly:
nvm install 24
nvm use 24

# 2. pnpm via Corepack (ships with Node)
corepack enable pnpm

# 3. uv (https://docs.astral.sh/uv/)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 4. Git for Windows: https://git-scm.com/download/win
```

## First-time project setup

Once the tools are installed, from the repo root:

```bash
# Make sure you're on the right Node version
nvm use                       # (Windows-native: nvm use 24)

# 1. Install JavaScript dependencies (frontend + TS libs)
pnpm install

# 2. Install Python dependencies and the matching Python version.
#    uv reads the project's pinned Python version and downloads it if missing.
uv sync

# 3. Activate the git hooks. THIS IS EASY TO FORGET.
#    Without it, commits skip linting/formatting/commit-message checks locally
#    and you'll get bounced by CI instead.
pnpm exec lefthook install
```

If `uv sync` complains it can't find a Python interpreter, run `uv python install` to let uv fetch one, then re-run `uv sync`.

## Daily commands

These all run from the repo root. Full table and explanation in [doc 02 — Monorepo and tooling](docs/teaching/02-monorepo-and-tooling.md).

| What you want | Command |
|---|---|
| Start the frontend dev server | `pnpm dev` |
| Start the backend dev server | `uv run fastapi dev apps/backend/main.py` |
| Run the scraper once | `uv run python -m scraper` |
| Run all linters | `pnpm lint` |
| Auto-format everything | `pnpm format` |
| Run all type checks | `pnpm check` |
| Run all tests | `pnpm test` |

## Before you commit

1. The git hooks (once installed) auto-format staged files and check your commit message. Let them.
2. Commit messages follow **Conventional Commits** — see [doc 08 — Git and PR workflow](docs/teaching/08-git-and-pr-workflow.md).
3. If a check fails, fix the code; don't bypass the hook with `--no-verify`. See [doc 09 — Quality gates](docs/teaching/09-quality-gates.md) for what each robot checks and why.

## Where to learn the architecture

Start with [`docs/teaching/`](docs/teaching/README.md). Read it in order the first time; after that, jump to the doc that matches your ticket. The single most important one is [doc 04 — Ports and adapters](docs/teaching/04-ports-and-adapters.md).
