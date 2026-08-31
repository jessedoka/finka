"""One-time Monzo OAuth setup — turns a confidential client into a permanent,
self-refreshing connection. After this, the daily snapshot auto-refreshes the
access token; you never paste a token again.

Prereq: register a CONFIDENTIAL OAuth client at developers.monzo.com with the
redirect URL below, giving you a client_id + client_secret.

Two steps (run in the api container):

  1) Start — stores the client creds and prints the authorise URL:
       docker compose exec -T api python -m scripts.monzo_auth \
           --client-id oauth2client_… --client-secret mnzconf…
     Open the printed URL, sign in, approve. Your browser lands on a
     can't-connect page whose address bar holds ?code=…&state=… — copy it.

  2) Finish — exchange the code for tokens:
       docker compose exec -T api python -m scripts.monzo_auth \
           --redirect-url "http://localhost:8000/monzo/callback?code=…&state=…"

  3) Approve the app in your Monzo phone app (Settings), then verify:
       docker compose exec -T api python -m scripts.monzo_auth --test
"""

import argparse
import asyncio
import secrets
import time
import urllib.parse as up

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from config import settings
from integrations.monzo import AUTH_URL, MonzoClient, MonzoError, exchange_token
from models.connection import Connection

REDIRECT_URI = "http://localhost:8000/monzo/callback"

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def _monzo_conn(db) -> Connection:
    conn = await db.scalar(select(Connection).where(Connection.provider == "monzo"))
    if conn is None:
        raise SystemExit("No Monzo connection found. Create one in the app first (any placeholder creds).")
    if conn.config is None:
        conn.config = {}
    return conn


async def start(client_id: str, client_secret: str) -> None:
    async with async_session() as db:
        conn = await _monzo_conn(db)
        state = secrets.token_urlsafe(16)
        conn.config.update({"client_id": client_id, "client_secret": client_secret, "_oauth_state": state})
        flag_modified(conn, "config")
        await db.commit()
    url = f"{AUTH_URL}?" + up.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": state,
    })
    print("Open this URL, sign in, and approve:\n")
    print(f"  {url}\n")
    print("Then copy the FULL redirected URL from your browser's address bar and run:")
    print('  … python -m scripts.monzo_auth --redirect-url "<paste it>"')


async def finish(redirect_url: str) -> None:
    q = up.parse_qs(up.urlparse(redirect_url).query)
    code = (q.get("code") or [None])[0]
    state = (q.get("state") or [None])[0]
    if not code:
        raise SystemExit("No ?code= found in that URL.")
    async with async_session() as db:
        conn = await _monzo_conn(db)
        cfg = conn.config
        if state and cfg.get("_oauth_state") and state != cfg["_oauth_state"]:
            raise SystemExit("State mismatch — start over with --client-id/--client-secret.")
        payload = await exchange_token({
            "grant_type": "authorization_code",
            "client_id": cfg.get("client_id"),
            "client_secret": cfg.get("client_secret"),
            "redirect_uri": REDIRECT_URI,
            "code": code,
        })
        cfg["access_token"] = payload["access_token"]
        cfg["refresh_token"] = payload["refresh_token"]
        cfg["monzo_expires_at"] = time.time() + int(payload.get("expires_in", 0))
        cfg.pop("_oauth_state", None)
        flag_modified(conn, "config")
        await db.commit()
    print("✓ Tokens stored on the Monzo connection.")
    print("NOW: open the Monzo app → approve the access request (Settings), then run --test.")


async def test() -> None:
    async with async_session() as db:
        conn = await _monzo_conn(db)
        cfg = conn.config
        client = MonzoClient(
            access_token=cfg.get("access_token"), account_id=cfg.get("account_id"),
            client_id=cfg.get("client_id"), client_secret=cfg.get("client_secret"),
            refresh_token=cfg.get("refresh_token"), expires_at=cfg.get("monzo_expires_at"),
        )
        try:
            value = await client.total_gbp()
        except MonzoError as e:
            raise SystemExit(f"✗ {e}")
        if client.refreshed:  # persist any rotation that happened during the test
            cfg["access_token"] = client.access_token
            cfg["refresh_token"] = client.refresh_token
            cfg["monzo_expires_at"] = client.expires_at
            flag_modified(conn, "config")
            await db.commit()
        print(f"✓ Monzo pots value: £{value}  (token auto-refresh working)")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id")
    ap.add_argument("--client-secret")
    ap.add_argument("--redirect-url")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        await test()
    elif args.redirect_url:
        await finish(args.redirect_url)
    elif args.client_id and args.client_secret:
        await start(args.client_id, args.client_secret)
    else:
        ap.error("Provide --client-id and --client-secret to start, --redirect-url to finish, or --test.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
