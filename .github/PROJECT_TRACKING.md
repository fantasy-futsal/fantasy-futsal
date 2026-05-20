# Fantasy Futsal - Project Tracking

**Last Updated**: 2026-05-20
**Created by**: Mistral Vibe (tomasvotava)

> **Note**: GitHub issues, milestones, and labels are the source of truth. This file only contains information without a dedicated source of truth elsewhere.

## Repository Structure

```
fantasy-futsal/
├── apps/
│   ├── frontend/          # SvelteKit + Tailwind
│   └── backend/           # FastAPI
├── libs/
│   ├── python/            # Shared Python libraries
│   │   └── database/      # Database port + adapters (SQLite, Firestore)
│   └── ts/                # Shared TypeScript libraries
├── docs/
│   └── adr/               # Architecture Decision Records
├── .github/
│   ├── workflows/         # GitHub Actions
│   └── PROJECT_TRACKING.md
├── package.json           # Root for pnpm workspaces
├── pyproject.toml         # Root for uv workspace
├── lefthook.yml
├── .eslintrc.json
├── .prettierrc
├── ruff.toml
├── mypy.ini
└── commitlint.config.js
```

## Decisions

| Decision | Value |
|----------|-------|
| Monorepo | pnpm + uv workspace |
| Backend Framework | FastAPI |
| Database Strategy | Port/Interface → SQLite → Firestore |
| Docker | Post-MVP |
| Shared Libraries | `libs/python/*` and `libs/ts/*` |

## Git Strategy

- **Branching**: Feature branches with rebase strategy
- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, etc.)
- **Merging**: Squash merge to main via PR with rebase
- **History**: Clean, linear history with meaningful commit messages

## Teaching Approach

### Key Principle: Database Abstraction First

Before implementing any database code, define the **port/interface**:

```python
# libs/python/database/port.py
from typing import Protocol, List
from dataclasses import dataclass

@dataclass
class Player:
    id: str
    name: str
    team: str
    position: str

class DatabasePort(Protocol):
    def save_players(self, players: List[Player]) -> None: ...
    def get_players(self) -> List[Player]: ...
    def get_player(self, player_id: str) -> Player | None: ...
```

Then student implements `SQLiteAdapter` (local dev) and later `FirestoreAdapter`.

### MVP Sequence (4 Sessions)

**Session 1** (Mentor + Student): Foundation
- Mentor: Monorepo setup, linting, CI, ADRs
- Student: Research futsalvplzni.cz

**Session 2** (Student-led): Scraper
- Student: Data models, typed scraper, error handling, JSON output
- Deliverable: Working scraper

**Session 3** (Together): Database + API
- Together: Define database port
- Student: SQLite adapter, FastAPI endpoints
- Together: Connect scraper → database → API
- Deliverable: Data accessible via API

**Session 4** (Student-led): Frontend
- Mentor: SvelteKit + Tailwind setup
- Student: Table component, API integration
- Deliverable: Browser table showing player data

**Result**: End-to-end pipeline working!

## ADRs to Create

1. **ADR-0001** - Selected Languages and Frameworks
2. **ADR-0002** - Monorepo Structure (pnpm + uv)
3. **ADR-0003** - Linting and Formatting Strategy
4. **ADR-0004** - Git Hooks and CI/CD
5. **ADR-0005** - CI/CD Strategy
6. **ADR-0006** - Database Abstraction Pattern

## Success Criteria

- [ ] Student can independently add new features after MVP
- [ ] Student understands the full stack (frontend to database)
- [ ] All code passes linting checks (ruff, mypy, ESLint, Prettier, commitlint)
- [ ] All ADRs are documented
- [ ] Student can explain architectural decisions
- [ ] Database abstraction allows easy switching from SQLite to Firestore
