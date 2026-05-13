from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.models.book import Book, CompleteBook
from src.models.job import Job
from src.models.user import User
from src.schema.response.book_response import BookDetailResponse


class BookListService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user

    async def get_user_books_with_details(
        self,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "id",
        sort_desc: bool = True,
        filter_name: str | None = None,
    ) -> list[BookDetailResponse]:
        cb_rn = (
            func.row_number()
            .over(partition_by=CompleteBook.book_id, order_by=CompleteBook.id.desc())
            .label("rn")
        )
        cb_subq = select(CompleteBook, cb_rn).subquery("cb_subq")
        complete_book_alias = aliased(CompleteBook, cb_subq)

        job_rn = (
            func.row_number()
            .over(partition_by=Job.object_id, order_by=Job.id.desc())
            .label("rn")
        )
        job_subq = (
            select(Job, job_rn).where(Job.object_table == "books").subquery("job_subq")
        )
        job_alias = aliased(Job, job_subq)

        books_stmt = select(Book).where(Book.user_id == self.current_user.id)

        if filter_name:
            books_stmt = books_stmt.where(Book.original_name.ilike(f"%{filter_name}%"))

        order_col = getattr(Book, sort_by, Book.id)
        books_stmt = books_stmt.order_by(
            desc(order_col) if sort_desc else asc(order_col)
        )

        books_stmt = books_stmt.limit(limit).offset(offset)
        books_subq = books_stmt.subquery("books_subq")
        book_alias = aliased(Book, books_subq)

        stmt = (
            select(book_alias, complete_book_alias, job_alias)
            .outerjoin(
                complete_book_alias,
                and_(complete_book_alias.book_id == book_alias.id, cb_subq.c.rn <= 20),
            )
            .outerjoin(
                job_alias,
                and_(job_alias.object_id == book_alias.id, job_subq.c.rn <= 20),
            )
            .order_by(desc(book_alias.id) if sort_desc else asc(book_alias.id))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        books_map: dict[int, BookDetailResponse] = {}

        for book_obj, cb_obj, job_obj in rows:
            if book_obj.id not in books_map:
                books_map[book_obj.id] = BookDetailResponse(
                    id=book_obj.id,
                    original_name=book_obj.original_name,
                    created_at=book_obj.created_at,
                    updated_at=book_obj.updated_at,
                )

            books_map[book_obj.id].add_complete_book(cb_obj)
            books_map[book_obj.id].add_job(job_obj)

        return list(books_map.values())
