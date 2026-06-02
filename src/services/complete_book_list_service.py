from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.book import Book, CompleteBook
from src.schema.response.book_response import CompleteBookResponse
from src.schema.response.response import PaginatedResponse, PaginationMeta


class CompleteBookListService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_complete_books(
        self,
        book: Book,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "id",
        sort_desc: bool = True,
    ) -> PaginatedResponse[CompleteBookResponse]:

        count_stmt = select(func.count(CompleteBook.id)).where(
            CompleteBook.book_id == book.id
        )
        total_count = await self.db.scalar(count_stmt) or 0

        if total_count == 0:
            return PaginatedResponse(
                data=[],
                meta=PaginationMeta(total=0, limit=limit, offset=offset),
            )
        base_stmt = select(CompleteBook).where(CompleteBook.book_id == book.id)

        sort_column = getattr(CompleteBook, sort_by, CompleteBook.id)
        order_clause = desc(sort_column) if sort_desc else asc(sort_column)

        stmt = base_stmt.order_by(order_clause)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        complete_books = result.scalars().all()

        data = [CompleteBookResponse.model_validate(book) for book in complete_books]

        return PaginatedResponse(
            data=data,
            meta=PaginationMeta(total=total_count, limit=limit, offset=offset),
        )
