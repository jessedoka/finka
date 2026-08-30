from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://finka:finka@db:5432/finka_dev"
    environment: str = "production"
    trading_212_key: str = "local"
    coinbase_api_key_name: str = ""
    coinbase_api_private_key: str = ""
    monzo_access_token: str = ""
    monzo_account_id: str = ""
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
