from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://finka:finka@db:5432/finka_dev"
    environment: str = "production"
    cognito_user_pool_id: str = "local"
    cognito_app_client_id: str = "local"
    aws_region: str = "eu-west-2"
    # --- Provider credentials: SEED-ONLY -------------------------------------
    # These are read exclusively by scripts/seed_connections.py, which turns them
    # into Connection rows on first run. Nothing else reads them: at runtime every
    # credential comes from the user's Connection config. Leave blank and add
    # sources through the Connections page instead.
    trading_212_key: str = "local"
    coinbase_api_key_name: str = ""
    coinbase_api_private_key: str = ""
    monzo_access_token: str = ""
    monzo_account_id: str = ""
    # Projection assumptions seeded onto the Monzo connection's config.
    # growth_rate is a fraction: 0.02 = 2%/yr.
    monzo_pots_monthly_contribution: float = 0.0
    monzo_pots_growth_rate: float = 0.0

    # Daily net-worth snapshot scheduler (in-container). Time is local 24h HH:MM.
    snapshot_scheduler_enabled: bool = True
    snapshot_time: str = "00:30"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        # Ignore unrecognised entries so a stale or extra variable in someone's
        # .env doesn't stop the app booting.
        extra = "ignore"

settings = Settings()
