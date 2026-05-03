import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv()


def get_database_url(is_async: bool = True) -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    driver = os.getenv("DB_DRIVER_ASYNC" if is_async else "DB_DRIVER")
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

    return f"{driver}://{user}:{password}@{host}:{port}/{db_name}"


SQLALCHEMY_DATABASE_URL_ASYNC = get_database_url(is_async=True)
engine = create_async_engine(SQLALCHEMY_DATABASE_URL_ASYNC, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

SQLALCHEMY_DATABASE_URL_SYNC = get_database_url(is_async=False)
sync_engine = create_engine(SQLALCHEMY_DATABASE_URL_SYNC, echo=False)
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


class Base(DeclarativeBase):
    pass
