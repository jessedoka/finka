from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://finka:finka@db:5432/finka_dev"
    environment: str = "production"
    cognito_user_pool_id: str = "local"
    cognito_app_client_id: str = "local"
    aws_region: str = "eu-west-2"

    class Config:
        env_file = Path(__file__).parent / ".env"

settings = Settings()
