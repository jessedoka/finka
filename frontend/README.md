# Finka frontend

Next.js (App Router) + React 19 + Tailwind 4 + shadcn/ui. Data fetching and caching
via TanStack Query. Lint and format with Biome.

| Route | What it shows |
|-------|---------------|
| `/dashboard` | Net-worth chart, spendable vs long-term vs committed split, projection |
| `/connections` | Add, test and sync data sources (form is generated from the API's provider manifest) |
| `/accounts` | Manual accounts for anything without an API |
| `/goals` | Savings goals with ring-fenced allocations |

```bash
npm install
npm run dev      # http://localhost:3000
npm run lint
npx tsc --noEmit
npm run build
```

The API base URL (`http://localhost:8000`) is hard-coded in [`lib/portfolio.ts`](lib/portfolio.ts).
See the [root README](../README.md) for the full setup and the design notes.
