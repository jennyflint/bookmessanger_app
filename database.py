import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


load_dotenv()


def get_database_url() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    if not all([user, password, db_name]):
        missing = [
            k
            for k, v in {
                "POSTGRES_USER": user,
                "POSTGRES_PASSWORD": password,
                "POSTGRES_DB": db_name,
            }.items()
            if not v
        ]
        err_msg = f"Missing environment variables: {', '.join(missing)}"
        raise ValueError(err_msg)

    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"
    return database_url


SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


class Base(DeclarativeBase):
    pass
