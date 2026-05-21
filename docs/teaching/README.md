# Teaching Docs

Welcome. These docs are written **for you, the student**, before you pick up your first ticket from the backlog. They are not API documentation or architecture decision records (those live in [`docs/adr/`](../adr/) once they exist) — they exist so that when you read an issue like "Implement SQLite adapter," you already understand what an adapter _is_ in this project and why we bothered making it pluggable.

Read them in order the first time. After that, jump to whichever one matches the ticket you're working on.

## How to read these

- Each file is a short "slide deck" in markdown. Skim the headings, then read the bits that aren't obvious.
- **Code blocks are examples**, not the final code. The point is the shape, not the line-by-line text. Your job on the ticket is to make it real.
- Every doc ends with a **"Tickets this prepares you for"** footer linking to GitHub issues by number. If a ticket is not in that list, the doc is probably not the right starting point.
- If something is unclear, that is a question for the mentor session — don't guess. Write it down.

## Reading order

| # | File | Read before working on... |
|---|------|---------------------------|
| 01 | [The big picture](01-the-big-picture.md) | Anything. This is the orientation. |
| 02 | [Monorepo and tooling](02-monorepo-and-tooling.md) | Your very first PR — even a one-line change. |
| 03 | [Typed Python](03-typed-python.md) | Defining data models (#16). |
| 04 | [Ports and adapters](04-ports-and-adapters.md) | Database port (#18) and SQLite adapter (#19). **The most important doc in this folder.** |
| 05 | [Scraping defensively](05-scraping-defensively.md) | Researching futsalvplzni.cz (#15) and the scraper (#17). |
| 06 | [REST API with FastAPI](06-rest-api-with-fastapi.md) | FastAPI endpoints (#20). |
| 07 | [Frontend data flow](07-frontend-data-flow.md) | Table component (#23) and player data display (#24). |
| 08 | [Git and PR workflow](08-git-and-pr-workflow.md) | Your very first PR. |
| 09 | [Quality gates](09-quality-gates.md) | The first time a lint hook fails on you (it will). |

## A note on tone

These docs assume:

- You know Python and HTML/CSS at a working level.
- You have not necessarily worked with `Protocol`, monorepos, REST API design, SvelteKit, or Conventional Commits before — so those get explained from scratch.
- You are going to write the code yourself. We do not paste finished implementations here; we paste the **shape** and explain the **why**.

If a doc explains something you already know, skim it and move on. If a doc explains something you don't know and it still doesn't make sense after a careful read, that's a signal to bring it to the mentor session — these docs are a starting point, not the whole conversation.
