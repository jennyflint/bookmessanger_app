from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.enums.export_book import ExportBookStatusEnum
from src.models.base import Base
from src.models.mixin import SoftDeleteMixin
from src.models.user import User


class Book(Base, SoftDeleteMixin):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="books")

    export_books: Mapped[list[ExportBook]] = relationship(
        "ExportBook", back_populates="book", cascade="all, delete-orphan"
    )


class ExportBook(Base):
    __tablename__ = "export_books"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=True)
    export_filename: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[ExportBookStatusEnum] = mapped_column(
        Enum(ExportBookStatusEnum, native_enum=False, length=40),
        default=ExportBookStatusEnum.NEW,
        nullable=False,
    )
    format: Mapped[FormatTypeEnum] = mapped_column(
        Enum(FormatTypeEnum, native_enum=False, length=40),
        nullable=False,
    )
    template: Mapped[TemplateTypeEnum] = mapped_column(
        Enum(TemplateTypeEnum, native_enum=False, length=40),
        nullable=True,
    )
    characters: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    book: Mapped[Book] = relationship(back_populates="export_books")
