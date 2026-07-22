# Finka — Developer Onboarding

> Read this first. It's the "day one" tour of the codebase: what Finka is, why it's
> built the way it is, and how a request flows from the browser all the way to a row
> in Postgres. When you're done you should be able to find your way around and add a
> feature without breaking the core ideas.
>
> This is the single source of truth for the codebase's architecture. (An older
> `ARCHITECTURE.md` described a pre-pivot transaction-tracking version and has been
> retired.)

---

## 1. What Finka is (and why it exists)

Finka is a **self-hosted personal net-worth dashboard**. You run it on your own
machine, connect your own financial data sources, and it tracks your **total net
worth over time** — with two extra ideas layered on top:

1. **Spendable vs. long-term.** Flag locked assets (pensions, LISAs, a house) so you
   can see what's *actually available now* versus your headline net worth.
2. **Projection.** A compound-growth forecast that rolls every source forward with
   monthly contributions and growth assumptions.

**The core problem it solves:** most providers (Trading212, Coinbase, a bank) will
tell you your balance *right now*, but almost none give you a "value over time"
history. Finka fixes this by **recording its own daily snapshot** of every source.
Day one is a single dot; over weeks it becomes a real chart. That snapshot idea is
the spine of the whole app — remember it.

**Why it's useful / important:**
- It's **provider-agnostic**. Finka ships with *no* accounts wired in. You bring your
  own sources, and anything that returns a number over HTTP can become one (more on
  this below). That's the design centrepiece.
- It's **private by construction**. Everything runs locally against your own Postgres.
  Credentials and balances never leave your machine.
- It's a **realistic full-stack system** to learn on: an async Python API, a plugin
  registry, a background scheduler, migrations, a typed React frontend, Docker — the
  same shapes you'd meet in a production cloud service (which is exactly the roadmap:
  the in-container scheduler is a stand-in for an eventual EventBridge → Lambda).

---

## 2. The 10,000-foot view

```
┌──────────────────────────┐        HTTP/JSON        ┌───────────────────────────┐
│  Next.js frontend         │  ───────────────────▶  │  FastAPI backend (api/)   │
│  (frontend/)              │                         │                           │
│  Dashboard · Connections  │  ◀───────────────────  │  routers → services →     │
│  · Accounts               │                         │  registry / selectors     │
└──────────────────────────┘                         └────────────┬──────────────┘
                                                                  │ SQLAlchemy (async)
                                                                  ▼
                                                       ┌───────────────────────┐
                                                       │  PostgreSQL           │
                                                       └───────────────────────┘
                                            ▲
        A daily in-container scheduler ─────┘  polls every source, writes one snapshot
```

Two deployables:

| Part | Tech | Location | Port |
|------|------|----------|------|
| **Backend API** | Python 3.11+ / FastAPI / SQLAlchemy (async) / Postgres | `api/` | 8000 |
| **Frontend** | Next.js (React) / TanStack Query / Tailwind / shadcn-ui | `frontend/` | 3000 |

Start everything with one command: `./dev.sh` (Postgres + API in Docker, migrations
applied, frontend launched). App at `http://localhost:3000`, API docs at
`http://localhost:8000/docs`.

---

## 3. The one idea to understand first: the provider registry

If you only internalise one thing, make it this. It's what makes "bring your own
source" work and it's why the rest of the codebase never hard-codes a bank.

**A *source* of money is data, not code.** Each source you connect is a row in the
`connections` table: a `provider` key + a `config` blob (its credentials/settings).
The **registry** ([api/integrations/registry.py](api/integrations/registry.py)) is a
small map from `provider key + config → one GBP number`.

```python
@dataclass(frozen=True)
class ProviderSpec:
    key: str                 # "monzo" | "trading212" | "coinbase" | "http"
    display_name: str        # shown in the UI dropdown
    fields: list[ProviderField]        # the config schema (drives the form + validation)
    fetch_gbp: Callable[[dict], Awaitable[Decimal]]  # config -> a GBP balance
    projection_fields: list[ProviderField]           # optional growth/contribution knobs
```

Because every provider is just a `ProviderSpec`, the whole system is driven off
`fields`:

- **The frontend form is generated** from the field list (`GET /api/connections/providers`
  returns the registry as JSON — a "manifest").
- **Validation** at connect-time uses the same fields (`missing_required`).
- **Aggregation** for net worth just loops over a user's connections and calls
  `spec.fetch_gbp(config)` — it never says the word "Monzo".
- **Secrets** are any field with `secret=True`; those are write-only everywhere.

### The two ways to add a source

1. **Generic HTTP connector (`http`)** — the general-purpose escape hatch. Point it at
   *any URL returning JSON with a number in it* and give a dotted `value_path`
   (e.g. `data.balance.amount`, or `accounts.0.balance` to index an array). The
   `_extract()` walker in the registry handles the path; a `multiplier` scales the
   result (e.g. `0.01` pennies→pounds). **No code change needed.**

2. **A named provider** — a purpose-built connector (Monzo, Trading212, Coinbase). Its
   `fetch_gbp` is a thin adapter over a mechanical client in
   [api/integrations/](api/integrations/). Adding one = registering **one more
   `ProviderSpec`** in `registry.py`. Everything else lights up automatically.

> **Mental model:** the registry is the plugin seam. The service layer is a generic
> engine that turns "a user's list of connections" into "a net-worth number". Providers
> plug into that engine; the engine knows nothing about any specific provider.

---

## 4. Data model (what's in Postgres)

Managed with SQLAlchemy models in [api/models/](api/models/) and Alembic migrations in
[api/alembic/versions/](api/alembic/versions/). The tables that matter for the current
(net-worth) app:

### `connections` — your data sources ([models/connection.py](api/models/connection.py))
The heart of the current design. One row per source.

| Column | Meaning |
|--------|---------|
| `provider` | registry key: `monzo` / `trading212` / `coinbase` / `http` |
| `label` | your name for it; also the breakdown key `conn:{label}` |
| `config` | JSON: credentials + settings (see registry field schema) |
| `is_active` | included in aggregation |
| `is_long_term` | excluded from the "spendable now" figure (still counts in total) |
| `last_synced_at` / `last_status` / `last_error` / `last_value` | **sync health** — written on every snapshot so the UI can show *why* a source isn't contributing (e.g. an expired token) instead of silently dropping it |

> ⚠️ `config` currently stores secrets **in plaintext** — fine for single-user
> self-hosting, flagged `TODO(encrypt)` in the model. Encrypt before any multi-tenant
> hosting.

### `net_worth_snapshots` — the history ([models/net_worth_snapshot.py](api/models/net_worth_snapshot.py))
One row **per user per day** (`(user_id, snapshot_date)` is unique). Holds
`total_assets`, `net_worth`, and a `breakdown` JSON — a per-source map like
`{"conn:Trading212": 12345.67, "account:Pension": 42000.0}`. **This is what the history
chart reads from.**

### `accounts` — manual sources ([models/account.py](api/models/account.py))
For anything without an API (a cash ISA, a pension you check quarterly). You type the
balance and keep it current. Carries the same projection knobs as connections
(`monthly_contribution`, `annual_charge`, `growth_rate`) and the `is_long_term` flag.

### `users` — owner of everything
Every other table hangs off a user; every query filters by `user_id` (multi-tenancy by
construction, even though there's one dev user today).

### Legacy tables (`transactions`, `categories`)
Still present from the transaction-tracking era with working CRUD, but **not part of
the current net-worth product**. Don't build new features on them without checking
they're still wanted.

---

## 5. Backend layering (how a request is handled)

The API is deliberately layered so each file has one job:

```
router  →  service  →  registry / query_selector  →  model  →  Postgres
(HTTP)     (logic)      (fetch a balance / build SQL)  (schema)
```

| Layer | Folder | Responsibility |
|-------|--------|----------------|
| **Router** | [api/routers/](api/routers/) | Parse the HTTP request, inject deps, return JSON. Thin. |
| **Service** | [api/services/](api/services/) | Business logic: ownership checks, aggregation, commits. |
| **Registry** | [api/integrations/](api/integrations/) | Map a provider+config to a GBP figure. |
| **Selectors** | [api/query_selectors/](api/query_selectors/) | Composable, chainable SQLAlchemy query builders. |
| **Schemas** | [api/schemas/](api/schemas/) | Pydantic request/response shapes (validation + serialisation). |
| **Models** | [api/models/](api/models/) | ORM classes = table definitions. |

Everything is **async** end-to-end (FastAPI handler → SQLAlchemy → asyncpg), and
resources are wired per-request via FastAPI's `Depends()` dependency injection
(`get_db` → a session, `get_service` → a service holding that session).

### The three services that do the real work

**`NetWorthService`** ([services/net_worth_service.py](api/services/net_worth_service.py)) — the engine.
- `_collect_balances()` — loops every active connection, calls the registry's
  `fetch_gbp`, and sums manual accounts. **A source that errors is logged, records its
  error in the health fields, and contributes 0 — it never sinks the whole snapshot.**
- `record_snapshot()` — aggregates everything and **upserts** today's snapshot (re-running
  the same day overwrites rather than colliding on the unique constraint).
- `get_current_breakdown()` — the live dashboard split. Clever bit: **connection values
  come from the last snapshot** (re-fetching every request would hit provider rate
  limits), but **manual accounts are read live** (cheap DB reads, so an edit shows
  immediately). It also computes `spendable` by excluding `is_long_term` sources.

**`ProjectionService`** ([services/projection_service.py](api/services/projection_service.py)) — the forecast.
Rolls each source forward month by month:
```
value = value * (1 + growth_rate/12) + monthly_contribution - annual_charge/12
```
Manual accounts use their DB columns; connections use knobs in their `config` (absent ⇒
held flat, so the projected total stays complete). Returns a yearly series plus a
"contributed vs. growth" split.

**`ConnectionService`** ([services/connection_service.py](api/services/connection_service.py)) — CRUD + the secret handling.
Two functions worth reading carefully:
- `redact_config()` — on **reads**, secret values are stripped and replaced with a
  `_secrets: {field: bool}` map (so the UI knows *which* secrets are set without ever
  seeing them).
- `merge_config()` — on **updates**, a secret the client omits is retained from storage
  (the frontend literally can't resend a value it was never given). This is why
  "editing a connection without re-entering the token keeps the token."
- `test()` — a **dry run**: fetch a balance from submitted config *without saving*, powering
  the "Test" button.

### Key endpoints (see `http://localhost:8000/docs` for the full list)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/connections/providers` | Registry manifest → drives the dynamic form |
| `GET/POST/PATCH/DELETE` | `/api/connections/…` | Manage sources (secrets write-only) |
| `POST` | `/api/connections/test` | Dry-run a config, return value or error |
| `GET` | `/api/net-worth/` | The daily history series (chart data) |
| `POST` | `/api/net-worth/snapshot` | **"Sync now"** — re-poll all sources, record today, return breakdown |
| `GET` | `/api/net-worth/breakdown` | Live per-source split (spendable vs long-term) |
| `GET` | `/api/net-worth/projection?years=N` | Compound-growth forecast |
| `GET` | `/api/accounts/…` | Manual account CRUD |
| `GET` | `/api/export/` | Full data export as a JSON download |

---

## 6. The daily scheduler (why the chart fills in)

[api/services/scheduler.py](api/services/scheduler.py) is a **dependency-free asyncio
loop** started from the FastAPI `lifespan` (see [api/main.py](api/main.py)): sleep until
the configured `SNAPSHOT_TIME` (default `00:30`), record a snapshot for the dev user,
repeat. One bad run is caught and logged; it never kills the loop. Toggle with
`SNAPSHOT_SCHEDULER_ENABLED`.

You don't have to wait for it: the **"Sync now"** button hits
`POST /api/net-worth/snapshot`, which does the same aggregation on demand. Adding a
source also auto-syncs.

> This loop is intentionally a **local stand-in** for a cloud EventBridge → Lambda
> schedule on the roadmap. It assumes the single dev user; when real auth lands it'll
> iterate over users.

---

## 7. Auth (currently stubbed)

[api/services/auth.py](api/services/auth.py) is built for **AWS Cognito JWT
validation** (fetch JWKS, verify `iss`/`client_id`/`token_use`, look up the user). But
when `ENVIRONMENT=development` it **short-circuits to a fixed dev user** (`dev-user-001`)
and skips tokens entirely. So today the app is effectively single-user; the Cognito
path is real code waiting to be switched on in production.

---

## 8. The frontend

Next.js app in [frontend/](frontend/). Three pages under [frontend/app/](frontend/app/):

- **Dashboard** ([app/dashboard/page.tsx](frontend/app/dashboard/page.tsx)) — composes
  cards: a stat strip, the net-worth-over-time chart (`PortfolioOverview`), the
  by-source `NetWorthBreakdown`, and the `ProjectionCard`.
- **Connections** ([app/connections/](frontend/app/connections/)) — add/edit/test sources.
  The form is **generated from the provider manifest**, so a new registry provider
  appears here with no frontend change.
- **Accounts** ([app/accounts/](frontend/app/accounts/)) — manual account CRUD.

All API calls and their TypeScript types live in one file:
[frontend/lib/portfolio.ts](frontend/lib/portfolio.ts) — a good place to see the whole
API surface from the client's side. Data fetching uses TanStack Query
(`components/queryProvider.tsx`); UI is Tailwind + shadcn-style primitives in
`components/ui/`.

> ⚠️ **Frontend gotcha:** [frontend/AGENTS.md](frontend/AGENTS.md) warns this is a
> non-standard Next.js with breaking changes — check `node_modules/next/dist/docs/`
> before writing frontend code rather than assuming conventions.

---

## 9. Running it locally

```bash
cp .env.example .env     # defaults are fine; you do NOT put provider keys here
./dev.sh                 # Postgres + API in Docker, migrations, then the frontend
```

- App: `http://localhost:3000` · API docs: `http://localhost:8000/docs`
- Credentials go in via the **Connections** page (stored in your DB), *not* `.env`.
  The provider vars in `.env.example` are a legacy convenience for
  `scripts/seed_connections.py`.

Manual/`uv`-based setup, tests, and DB management are in [SETUP.md](SETUP.md). Common:

```bash
cd api
uv run pytest                 # run the backend tests (tests/)
uv run alembic upgrade head   # apply migrations
uv run alembic revision --autogenerate -m "…"   # after changing a model
```

Tests worth knowing: [tests/test_registry.py](api/tests/test_registry.py) (the plugin
seam) and [tests/test_connection_service_helpers.py](api/tests/test_connection_service_helpers.py)
(the redact/merge secret logic) cover the current core.

---

## 10. Where things live (cheat sheet)

```
finka/
├── api/
│   ├── main.py                  # FastAPI app + lifespan (starts the scheduler)
│   ├── config.py                # env-driven Settings singleton
│   ├── integrations/
│   │   ├── registry.py          # ★ the plugin seam: ProviderSpec map
│   │   ├── monzo.py trading212.py coinbase.py   # mechanical per-provider clients
│   ├── models/                  # connection, net_worth_snapshot, account, user (+ legacy)
│   ├── routers/                 # connections, net_worth, accounts, export, …
│   ├── services/                # net_worth, projection, connection, scheduler, auth
│   ├── query_selectors/         # composable SQLAlchemy query builders
│   ├── schemas/                 # Pydantic DTOs
│   ├── alembic/versions/        # migrations
│   └── scripts/                 # seed, reset, snapshot, seed_connections
├── frontend/                    # Next.js app (dashboard, connections, accounts)
│   └── lib/portfolio.ts         # all API calls + TS types in one place
├── dev.sh                       # one-command local start
├── docker-compose.yml           # Postgres + API
├── README.md                    # user-facing "how to run + connect sources"
└── ONBOARDING.md                # ← you are here (architecture + dev tour)
```

---

## 11. Current status & good first tasks

**Working today:** connections CRUD with write-only secrets, the generic HTTP + three
named providers, daily + on-demand snapshots, live breakdown with spendable/long-term
split, projection, manual accounts, full JSON export, the dashboard.

**Deliberately stubbed / not yet done:**
- **Auth** — dev-user short-circuit; the Cognito path exists but isn't the live flow.
- **Secret encryption** — `config` is plaintext (`TODO(encrypt)`).
- **Multi-user** — everything is keyed by `user_id`, but the scheduler and dev-user
  assume one user.
- **Cloud scheduler** — the asyncio loop is a local stand-in for EventBridge → Lambda.

**Good ways to get your hands dirty:**
1. **Add a named provider** — write a `ProviderSpec` in `registry.py` (reuse the generic
   HTTP mechanics or add a client in `integrations/`). Watch it appear in the UI with no
   frontend change. This teaches you the whole spine.
2. Trace one "Sync now" click from `frontend/lib/portfolio.ts` → `POST /api/net-worth/snapshot`
   → `NetWorthService.record_snapshot` → registry → Postgres.
3. Read `redact_config` / `merge_config` in `connection_service.py` and the tests around
   them — the secret-handling contract is subtle and important.
```
