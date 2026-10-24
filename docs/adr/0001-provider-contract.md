# ADR 0001: Providers are separate packages behind one failure-safe contract

- Status: Accepted
- Date: 2026-10-24

## Context and Problem Statement

Finka is a local portfolio tracker. It pulls balances from several sources (Monzo, Coinbase, Trading212, any JSON API) and adds them into one net worth figure, so there is no manual adding up across apps.

It was first designed to be hosted on AWS (Cognito for sign-in, RDS for the database). That plan was dropped. Hosting was too costly to keep running, and storing bank credentials in the cloud was a risk. Running locally keeps the data private and owned by the user, lets snapshots be kept, and means the database is Postgres on the user's own machine.

Going local raised the question this ADR answers: how does Finka get a balance from many different sources, and what happens when one of them fails? Today, a failed source adds 0 to that snapshot. The connection records `last_status="error"` and `last_error` so the UI can show why, and the UI shows the understated total.

## Decision Drivers

- **Local-first and private.** No hosting. Bank credentials stay on the user's machine. Saved data can be viewed without internet.
- **Modular.** Each bank or asset is its own package, so a user picks the assets they want and manages them over time.
- **Small core.** Core stays generic and never names a specific bank. Dropping Monzo should not mean editing core.
- **Failure isolation.** One broken source must not break the rest.

## Considered Options

1. **Hardcoded clients reading keys from `.env`** (v1, 18 Jul 2026). Rejected: one user, one instance, and adding a bank meant code changes and a redeploy.
2. **All providers in one registry inside core** (v2, 22 Jul 2026). Rejected: the logic for every provider was fixed inside core. Providers should be a customisation, not core code.
3. **Host on AWS** (original plan). Rejected: it is not local-first. It costs money to run and puts bank credentials in the cloud.

## Decision Outcome

Chosen option: **separate provider packages behind one contract**, because it keeps core generic and lets each provider be added or removed without touching core.

- A source is a database row (provider plus config), not code. The code drives what the UI shows, and a provider is something that code can load, use and display.
- Every provider is called through `ProviderSpec.fetch_gbp`, which raises only `ProviderError`. This is enforced in one place, so a new provider cannot leak raw errors.
- Each provider is its own package, found through entry points.

Providers return one value in pounds, which is what makes the figures summable. A provider has to convert to pounds itself, and the generic HTTP connector has a `multiplier` field for that.

## Consequences

**Good**

- Adding or removing a provider needs no change to core.
- One failing source cannot crash a snapshot.

**Bad / trade-offs**

- A failed source counts as £0, so that day's snapshot is understated.
- Setup needs some technical knowledge, so it is harder to get into at first.
- Few providers exist so far, and they are bundled with the repo, not yet installable by third parties.
- Secrets are stored as-is in the database.
- No FX conversion is built in.
