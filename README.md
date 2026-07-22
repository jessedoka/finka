# Finka

A self-hosted personal net-worth dashboard. You run it, you connect your own data
sources, and it tracks your total net worth over time — with a spendable-vs-locked
split and a savings projection.

Finka doesn't ship with any accounts wired in. **You bring your own sources.** If a
provider has a read-only API (or any endpoint that returns your balance as JSON),
Finka can poll it. For anything without an API, add a manual account and keep the
number up to date by hand.

---

## What you get

- **Net worth over time** — a daily snapshot of every connected source, charted.
- **By-source breakdown** — where your money actually is.
- **Spendable vs long-term** — flag locked assets (pensions, LISAs, anything you
  can't touch) so you can see what's actually available now.
- **Projection** — compound-growth forecast with monthly contributions.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker + Docker Compose | v2+ | Runs Postgres + the API |
| Node.js | 20+ | Runs the frontend |
| npm | 10+ | Comes with Node |

---

## Quick start

```bash
git clone <your-fork-url> finka
cd finka
cp .env.example .env      # the defaults are fine for local use
./dev.sh
```

`dev.sh` starts Postgres + the API in Docker, applies database migrations, and
launches the frontend. When it's up:

- **App:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

> **Do I need to edit `.env`?** No. The defaults run everything locally. You do
> **not** put any provider API keys in `.env` — credentials are added per-source
> through the app's **Connections** page (below), where they're stored in your
> database rather than a config file. The provider variables in `.env.example` are
> a legacy convenience (see [Seeding sources from `.env`](#optional-seeding-sources-from-env))
> and can be left blank.

If you'd rather not use `dev.sh`, see [Manual setup](#manual-setup).

---

## Connecting your data

Open the app and go to the **Connections** tab. Every source you add starts
contributing to your net worth on the next sync.

### Option 1 — Generic HTTP connector (works with anything)

This is the general-purpose path: point Finka at **any URL that returns JSON with a
number in it**, and it polls that number as a GBP balance. Great for a bank/broker
with a read-only API, a self-hosted service, a crypto exchange, a spreadsheet
published as JSON — anything.

On the Connections page, pick **Generic HTTP (JSON)** and fill in:

| Field | What it is | Example |
|-------|-----------|---------|
| **URL** | The endpoint returning JSON | `https://api.example.com/v1/account` |
| **Value path** | Dotted path to the number in the response | `data.balance.amount` |
| **Method** | `GET` (default) or `POST` | `GET` |
| **Headers** | JSON object of headers, e.g. for auth (write-only/secret) | `{"Authorization": "Bearer YOUR_TOKEN"}` |
| **Multiplier** | Scales the value — e.g. `0.01` to turn pennies into pounds | `1` |

**Worked example.** Say your provider responds to `GET https://api.example.com/v1/account` with:

```json
{
  "status": "ok",
  "data": {
    "balance": { "amount": "12345.67", "currency": "GBP" }
  }
}
```

Then set **Value path** to `data.balance.amount`. Paths walk objects and arrays by
index — e.g. `accounts.0.balance` reads the balance of the first item in an
`accounts` array.

Hit **Test** before saving to confirm Finka can reach the endpoint and pull the
number. On success it shows the fetched value; on failure it tells you what went
wrong (bad path, auth rejected, not JSON, …).

> **Currency:** Finka treats the fetched number as GBP. There's no FX conversion —
> if your source is in another currency, either pre-convert it or set the
> **Multiplier** to an approximate rate.

### Option 2 — Named integrations

Finka also ships purpose-built connectors for a few providers. They appear in the
same **Provider** dropdown and ask for that provider's specific credentials (an API
key, a token, etc.) instead of a raw URL. Each field has inline help pointing to
where you generate the credential. Use these if your provider is in the list;
otherwise the Generic HTTP connector above covers it.

Adding a new named integration is a code change — register one `ProviderSpec` in
[`api/integrations/registry.py`](api/integrations/registry.py) and it shows up
everywhere automatically (form, validation, aggregation). PRs welcome.

### Option 3 — Manual accounts

For anything without an API — a cash ISA, a pension you check quarterly, property —
use the **Manual Accounts** tab. You type the balance and update it whenever it
changes. Manual accounts support the same projection inputs (monthly contribution,
growth rate, annual charge) and the spendable/long-term flag.

---

## Using it

- **Secrets are write-only.** Once you save a connection, its secret fields (tokens,
  keys, auth headers) are never shown again — the app only tells you whether a
  secret is set. Editing a connection without re-entering a secret keeps the stored
  one.
- **Sync now.** Balances refresh on a daily snapshot, but you don't have to wait:
  the **Sync now** button on the Connections page re-polls every source immediately
  and updates the dashboard. Adding a source auto-syncs it.
- **Health.** Each connection shows its last sync status — the fetched value and
  time on success, or the error (e.g. an expired token) on failure. A source that
  fails contributes 0 and stays visible with the reason, rather than silently
  vanishing.
- **Spendable vs long-term.** Toggle any source or account to **Long-term** to
  exclude it from the "spendable now" figure while keeping it in total net worth.

---

## Manual setup

If you're not using `dev.sh`:

```bash
# 1. Database + API (Docker)
docker compose up -d --build

# 2. Migrations
docker compose exec api alembic upgrade head

# 3. Frontend
cd frontend
npm install
npm run dev
```

- App: http://localhost:3000 · API: http://localhost:8000

Optionally seed a dev user and two sample manual accounts so the dashboard has
something to render:

```bash
docker compose exec api python scripts/seed.py
```

### Running the API outside Docker

Requires Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/). Start Postgres on
its own (`docker compose up db -d`), or point `DATABASE_URL` at any Postgres 16.

```bash
cd api
uv sync                                  # install dependencies
uv run alembic upgrade head              # migrations
uv run uvicorn main:app --reload --port 8000
```

### Database management

| Task | Command (from `api/`) |
|------|-----------------------|
| Apply pending migrations | `uv run alembic upgrade head` |
| Roll back one migration | `uv run alembic downgrade -1` |
| Generate a migration | `uv run alembic revision --autogenerate -m "description"` |
| Reset to an empty DB | `uv run python scripts/reset.py` |

### Tests and linting

```bash
cd api
uv run pytest
uv run ruff check .

cd ../frontend
npm run lint
npx tsc --noEmit
```

---

## Optional: seeding sources from `.env`

If you'd prefer to configure a named provider's credentials as environment
variables instead of through the UI (e.g. for a scripted deploy), fill in the
relevant variables in `.env`, then run:

```bash
docker compose exec api python -m scripts.seed_connections
```

This creates connection rows from whatever provider variables are set. It's
idempotent — it skips a provider you already have a connection for — and is purely a
convenience; the UI is the normal way to add sources.

---

## How it works

- Each source you connect is a **Connection** row (provider + your config). A daily
  in-container scheduler records a **net-worth snapshot** — one GBP figure per source
  — which is what the history chart and by-source breakdown read from.
- Provider logic lives behind a small **registry** ([`api/integrations/registry.py`](api/integrations/registry.py)),
  so the rest of the app never hard-codes a provider. That's what makes the Generic
  HTTP connector and any future integration drop-in.
- Everything runs locally against your own Postgres. Your credentials and balances
  never leave your machine.

---

## Roadmap

Ideas being considered, not commitments.

### Fewer provider-specific integrations

The named connectors carry more bespoke code than they need to. Looking at what each
one actually requires beyond a plain HTTP GET:

| Provider | Needs beyond a plain GET |
|----------|--------------------------|
| Trading212 (balance) | **Nothing** — the generic HTTP connector already covers it |
| Monzo | One arithmetic step: subtracting two fields of the same response |
| Coinbase | Genuinely irreducible — per-request JWT signing, pagination, per-asset valuation |

So one of the three needs real code, one needs a small generic feature, and one needs
none at all. The direction that suggests is **presets rather than plugins**: a named
entry in the provider dropdown becomes a *pre-filled generic-HTTP config shipped as
data*, so you still pick "Trading212" and fill in just your API key — but no bespoke
client exists behind it. Code stays reserved for providers that genuinely can't be
expressed declaratively (anything doing request signing).

### Candidate generic capabilities

Each of these would let a preset replace a hand-written client, and each is useful to
*any* source rather than being one provider's special case:

- **Auth styles** — bearer token, raw header, query parameter, rather than hand-typed
  header JSON.
- **Derived values** — sum or subtract across several value paths in one response.
- **Retry/backoff** on `429`, which today only the Trading212 client does.

### Open questions

- What happens to the Trading212 positions/P&L panel? It needs more than one balance
  number, so it either becomes a general "holdings" capability, or goes away.
- Should signed-request providers stay in-tree, or move to optional plugin packages
  installed separately?
- How far should the declarative schema go before it becomes a DSL with its own
  maintenance and documentation burden? Past a point, code is the simpler answer.

The [`ProviderSpec`](api/integrations/registry.py) seam already makes either path
possible without touching the rest of the app.

## Project layout

```
finka/
├── api/                     # FastAPI backend
│   ├── integrations/        # Provider registry + per-provider clients
│   ├── models/ routers/ services/ schemas/
│   ├── alembic/             # DB migrations
│   ├── scripts/             # seed, reset, snapshot, seed_connections
│   └── tests/
├── frontend/                # Next.js app (Connections, Accounts, Dashboard)
├── docker-compose.yml
└── dev.sh                   # one-command local start
```
