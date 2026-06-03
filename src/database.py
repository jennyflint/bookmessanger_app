from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, event, true
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    ORMExecuteState,
    Session,
    sessionmaker,
    with_loader_criteria,
)

from src.models.base import Base
from src.settings.settings import db_settings


engine = create_async_engine(db_settings.async_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


sync_engine = create_engine(db_settings.sync_url, echo=False)
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


@event.listens_for(Session, "do_orm_execute")
def intercept_async_orm_execute(execute_state: ORMExecuteState) -> None:
    """
    Intercept ORM execute to apply soft delete filter.
    For off use: .execution_options(include_deleted=True)
    """

    if execute_state.is_select and not execute_state.execution_options.get(
        "include_deleted", False
    ):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                Base,
                lambda cls: (
                    cls.deleted_at.is_(None) if hasattr(cls, "deleted_at") else true()
                ),
                include_aliases=True,
            )
        )
