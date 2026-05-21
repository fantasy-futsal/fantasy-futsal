# 07 — Frontend Data Flow

> Read before building the table component (#23) and the player data display (#24).

## What SvelteKit gives you

SvelteKit is a framework on top of Svelte (the component model). Svelte is "how do I write a button"; SvelteKit is "how do I organize a whole app — routes, data loading, layouts, server/client split."

A few things to internalize before writing code:

- **File-based routing.** A file at `src/routes/players/+page.svelte` becomes the page at `/players`. The folder name is the URL. No `Router` component, no route configuration.
- **A `+page.svelte` is a Svelte component.** That's the visible piece — HTML, CSS, and Svelte syntax.
- **A `+page.ts` or `+page.server.ts` next to it loads data for that page** before the component renders. This is the part that fetches from our FastAPI backend.
- **Layouts wrap pages.** `+layout.svelte` is the persistent shell (nav bar, footer) that wraps every page in its folder and below.

You don't need to deeply understand Svelte 5 runes (`$state`, `$derived`, etc.) to do the MVP table — they matter more when state gets interactive. For now: file-based routes + load functions + a component to render the data.

## The data flow, end-to-end

```
   User opens /players in browser
              │
              ▼
   ┌──────────────────────┐
   │  +page.ts            │   runs first (in browser, or on server during SSR)
   │  load() {            │
   │    fetch /players    │ ──→ FastAPI returns JSON
   │  }                   │
   └─────────┬────────────┘
             │  returns { players: [...] }
             ▼
   ┌──────────────────────┐
   │  +page.svelte        │
   │  let { data } = $props()
   │  <PlayerTable        │
   │    players={data.players}
   │  />                  │
   └─────────┬────────────┘
             │
             ▼
   ┌──────────────────────┐
   │  PlayerTable.svelte  │   the actual <table> markup
   │  in src/lib/         │
   └──────────────────────┘
```

The split matters: **fetching lives in `+page.ts`**, **rendering lives in `+page.svelte` and components**. Don't fetch from inside a component — components should be "given data, render data" and that's it.

## A worked example

### `+page.ts` — the load function

```ts
// apps/frontend/src/routes/players/+page.ts
import type { PageLoad } from './$types';

export interface Player {
	id: string;
	name: string;
	team: string;
	position: string;
}

export const load: PageLoad = async ({ fetch }) => {
	const response = await fetch('http://localhost:8000/players');
	if (!response.ok) {
		throw new Error(`Failed to load players: ${response.status}`);
	}
	const players: Player[] = await response.json();
	return { players };
};
```

A few things:

- **Use the `fetch` passed in via the argument**, not the global `window.fetch`. SvelteKit gives you a special `fetch` that works during server-side rendering, handles cookies properly, and avoids double-fetching.
- **Type the response.** `Player[]` is the contract with the backend. Eventually we'll generate these types from the OpenAPI spec; for now, hand-write them and keep them in sync with `PlayerResponse` in `apps/backend/schemas.py`.
- **The hardcoded URL is a placeholder.** Production deploys won't use `localhost:8000`. We'll pull this into an env var (`PUBLIC_API_URL`) when that becomes a real concern — not before.
- **Errors thrown from `load` become error pages.** SvelteKit has a `+error.svelte` convention for rendering them.

### `+page.svelte` — the page component

```svelte
<!-- apps/frontend/src/routes/players/+page.svelte -->
<script lang="ts">
	import PlayerTable from '$lib/PlayerTable.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<h1 class="text-2xl font-bold mb-4">Players</h1>
<PlayerTable players={data.players} />
```

- `data` is the value returned from `load()`. SvelteKit types it for you via `PageData`.
- `$props()` is the Svelte 5 runes syntax for "this component's props." If you see older `export let data` syntax in tutorials, that's the pre-runes way — this project is runes mode.
- The `class="text-2xl font-bold mb-4"` is Tailwind. We compose styles by stacking utility classes rather than writing custom CSS.

### `PlayerTable.svelte` — the reusable component

```svelte
<!-- apps/frontend/src/lib/PlayerTable.svelte -->
<script lang="ts">
	interface Player {
		id: string;
		name: string;
		team: string;
		position: string;
	}

	let { players }: { players: Player[] } = $props();
</script>

<table class="min-w-full border-collapse">
	<thead>
		<tr class="border-b text-left">
			<th class="p-2">Name</th>
			<th class="p-2">Team</th>
			<th class="p-2">Position</th>
		</tr>
	</thead>
	<tbody>
		{#each players as player (player.id)}
			<tr class="border-b">
				<td class="p-2">{player.name}</td>
				<td class="p-2">{player.team}</td>
				<td class="p-2">{player.position}</td>
			</tr>
		{/each}
	</tbody>
</table>
```

- **`$lib`** is SvelteKit's alias for `src/lib/`. Anything you want to import from multiple places goes there.
- **`{#each players as player (player.id)}`** — the `(player.id)` is a "keyed each block." It tells Svelte how to identify items so it can re-render efficiently when the list changes. Always provide a key on lists.
- The component takes `players: Player[]` and renders them. It does not fetch. It does not know there's a backend. **It would still work if we passed in hard-coded test data**, which is exactly what its unit test will do.

## Where things go

| Kind of file | Where |
|---|---|
| A page (a URL the user can visit) | `src/routes/<path>/+page.svelte` (+ `+page.ts` if it needs data) |
| A shared component (used by 2+ pages or 2+ components) | `src/lib/<Name>.svelte` |
| A shared TypeScript type/util | `src/lib/<name>.ts` |
| Global CSS | `src/routes/layout.css` (already exists) |
| Static assets (favicon, images) | `static/` |

The same rule as in [doc 02](02-monorepo-and-tooling.md) applies: **don't pre-emptively put a component in `$lib/` just because it might be reused.** Start in the route that needs it; move when a second user appears.

## SSR vs client-side rendering

By default, `+page.ts` runs during **server-side rendering** (SSR) on the first page load, then on the client for subsequent navigations. This is mostly a magic-it-just-works thing for our app, but two things to know:

- **Don't reach for `window` or `document` inside a `load` function.** It runs on the server first; those don't exist there. If you need browser-only logic, put it inside a component's lifecycle (e.g. `$effect` in runes mode).
- **If you specifically need server-only logic** (e.g. an API key that must not ship to the browser), use `+page.server.ts` instead. That file _only_ ever runs on the server.

For the MVP, plain `+page.ts` is the right default.

## Common pitfalls

### Fetching inside a component

```svelte
<!-- DON'T -->
<script>
  let players = $state([]);
  fetch('/players').then(r => r.json()).then(p => players = p);
</script>
```

This works, but:

- The first render shows an empty table while the fetch is in flight (no SSR data).
- Every component instance re-fetches.
- It's harder to test — the component now depends on `fetch` working.

Use a `load` function. The component receives ready data and stays pure.

### Letting the table component know about the backend

A `PlayerTable` that says `fetch('/players')` inside it is not reusable. The whole point of separating "fetch" from "render" is that the table works with any list of players — from the API, from a mock in a test, from a fixture in Storybook. Keep components ignorant of where their data came from.

### Hardcoding API URLs across many files

For the MVP, `http://localhost:8000` in one place is fine. The moment you have it in three files, pull it out into a constant (or env var, once we have deploys). Find/replace cleanups are a code smell — the original author should've named the thing.

### Forgetting the `(key)` on `{#each}`

`{#each players as player}` without a key works, but when the list changes Svelte may re-render more than necessary (and lose component state like form input values). Always pass a stable identifier: `{#each players as player (player.id)}`.

### Skipping types because "it's just frontend"

It isn't. The frontend and backend both have a `Player` shape; if they drift, the user sees a broken table at runtime instead of you seeing a red squiggle at compile time. Type your `load()` return values and your component props. ESLint and `svelte-check` will help you catch the gaps.

## Tickets this prepares you for

- **#22 — Setup SvelteKit with Tailwind** (mentor task, already done — this is why `apps/frontend/` exists and Tailwind works out of the box)
- **#23 — Create reusable table component** (yours — `PlayerTable.svelte` in `src/lib/`)
- **#24 — Fetch and display player data in frontend** (yours — `+page.ts` + `+page.svelte` for `/players`)
