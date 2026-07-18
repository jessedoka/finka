from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://finka:finka@db:5432/finka_dev"
    environment: str = "production"
    cognito_user_pool_id: str = "local"
    cognito_app_client_id: str = "local"
    aws_region: str = "eu-west-2"
    trading_212_key: str = "local"

    # Coinbase (read-only). CDP API key: a key *name/id* plus a PEM private key
    # used to sign a short-lived JWT per request. Empty => integration skipped.
    coinbase_api_key_name: str = ""
    coinbase_api_private_key: str = ""

    # Monzo (read-only). Direct access token from the Monzo developer playground
    # (https://developers.monzo.com/), plus the account id to read. NOTE: these
    # playground tokens EXPIRE after a few hours and can't be auto-refreshed —
    # paste a fresh one when it goes stale. Empty access_token => skipped.
    monzo_access_token: str = ""
    monzo_account_id: str = ""
    monzo_user_id: str = ""  # reserved for future /transactions use; unused for balance
    # Projection assumptions for Monzo pots (a live source, so not a manual Account).
    # growth_rate is a fraction: 0.02 = 2%/yr.
    monzo_pots_monthly_contribution: float = 0.0
    monzo_pots_growth_rate: float = 0.0

    # Daily net-worth snapshot scheduler (in-container). Time is local 24h HH:MM.
    snapshot_scheduler_enabled: bool = True
    snapshot_time: str = "00:30"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"

settings = Settings()
