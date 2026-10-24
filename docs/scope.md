# Scope (frozen 2026-10-24)

Rule: no new features. Only fixes that block a flow or a fresh clone.

## In
- Provider contract: one error type, entry-point discovery of bundled providers (ADR 0001)
- Providers: Monzo, Coinbase, Trading212, generic HTTP
- Pages: net worth, goals, projection, connections, export, theme editor
- Failure isolation: a broken source never sinks a snapshot
- Local-first, single user: `./start.sh` runs everything
- Tests, ruff, CI (GitHub Actions)

## UI revamp (timeboxed)
- Visual polish only: layout, spacing, colour, net worth page first
- No new pages, no new data, no API changes
- Hard stop: 16:00 Sat 24 Oct. Unfinished work stays as it is.

## Deferred (goes in README)
- Real auth (single local user by design; Cognito removed)
- Encrypting provider secrets at rest (stored as-is in the DB)
- Staleness flag: a failed source counts as 0 in that snapshot
- Retry / backoff on provider calls
- FX conversion (only a `multiplier` workaround)
- Third-party installable providers (today they are bundled workspace packages discovered via entry points; a documented install path is future work)
