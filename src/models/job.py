from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base


class JobStatusEnum(enum.StrEnum):
    NEW = "new"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobTypeEnum(enum.StrEnum):
    BOOK_PARSING = "book_parsing"


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    object_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    object_table: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    status: Mapped[JobStatusEnum] = mapped_column(
        Enum(JobStatusEnum, native_enum=False, length=40),
        default=JobStatusEnum.NEW,
        nullable=False,
    )

    type: Mapped[JobTypeEnum] = mapped_column(
        Enum(JobTypeEnum, native_enum=False, length=40), nullable=False
    )

    count_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_jobs_object_table_id", "object_table", "object_id"),)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.object_table}, status={self.status})>"
