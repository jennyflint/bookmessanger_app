from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base
from src.enums.enums import FormatTypeEnum
from src.models.user import User


class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="books")

    complete_books: Mapped[list[CompleteBook]] = relationship(
        "CompleteBook", back_populates="book", cascade="all, delete-orphan"
    )


class CompleteBook(Base):
    __tablename__ = "complete_books"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_expired: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    format: Mapped[FormatTypeEnum] = mapped_column(
        Enum(FormatTypeEnum, native_enum=False, length=40),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    book: Mapped[Book] = relationship(back_populates="complete_books")
