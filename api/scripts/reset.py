import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import settings
from models import Base

engine = create_async_engine(settings.database_url)

async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        print("Dropped all tables.")

    await engine.dispose()

    import subprocess
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Migrations applied.")

    from scripts.seed import seed
    await seed()
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(reset())