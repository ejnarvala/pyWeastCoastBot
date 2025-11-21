import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Convert postgres:// to postgresql+asyncpg://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return database_url

    # Default to SQLite
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    db_dir = Path("/app/data") if os.path.exists("/app/data") else base_dir
    db_path = db_dir / "db.sqlite3"
    return f"sqlite+aiosqlite:///{db_path}"


engine: AsyncEngine = create_async_engine(
    get_database_url(),
    echo=False,
    future=True,
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
