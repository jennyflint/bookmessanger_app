from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.book import Book, ExportBook
from src.schema.response.book_response import ExportBookResponse
from src.schema.response.response import PaginatedResponse, PaginationMeta


class ExportBookListService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_export_books(
        self,
        book: Book,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "id",
        sort_desc: bool = True,
    ) -> PaginatedResponse[ExportBookResponse]:

        count_stmt = select(func.count(ExportBook.id)).where(
            ExportBook.book_id == book.id
        )
        total_count = await self.db.scalar(count_stmt) or 0

        if total_count == 0:
            return PaginatedResponse(
                data=[],
                meta=PaginationMeta(total=0, limit=limit, offset=offset),
            )
        base_stmt = select(ExportBook).where(ExportBook.book_id == book.id)

        sort_column = getattr(ExportBook, sort_by, ExportBook.id)
        order_clause = desc(sort_column) if sort_desc else asc(sort_column)

        stmt = base_stmt.order_by(order_clause)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        export_books = result.scalars().all()

        data = [
            ExportBookResponse.model_validate(export_book)
            for export_book in export_books
        ]

        return PaginatedResponse(
            data=data,
            meta=PaginationMeta(total=total_count, limit=limit, offset=offset),
        )
