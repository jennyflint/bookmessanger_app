from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.models.book import Book
from src.models.job import Job
from src.models.user import User
from src.schema.response.book_response import BookDetailResponse
from src.schema.response.response import PaginatedResponse, PaginationMeta


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
    ) -> PaginatedResponse[BookDetailResponse]:

        base_stmt = select(Book).where(
            and_(Book.user_id == self.current_user.id, Book.deleted_at.is_(None))
        )
        if filter_name:
            base_stmt = base_stmt.where(Book.original_name.ilike(f"%{filter_name}%"))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_count_res = await self.db.execute(count_stmt)
        total_count = total_count_res.scalar() or 0

        order_col = getattr(Book, sort_by, Book.id)
        books_stmt = (
            base_stmt.order_by(desc(order_col) if sort_desc else asc(order_col))
            .limit(limit)
            .offset(offset)
        )

        books_subq = books_stmt.subquery("books_subq")
        book_alias = aliased(Book, books_subq)

        job_rn = (
            func.row_number()
            .over(partition_by=(Job.object_id, Job.type), order_by=Job.id.desc())
            .label("rn")
        )
        job_subq = (
            select(Job, job_rn).where(Job.object_table == "books").subquery("job_subq")
        )
        job_alias = aliased(Job, job_subq)

        stmt = (
            select(book_alias, job_alias)
            .outerjoin(
                job_alias,
                and_(job_alias.object_id == book_alias.id, job_subq.c.rn <= 20),
            )
            .order_by(desc(book_alias.id) if sort_desc else asc(book_alias.id))
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        books_map: dict[int, BookDetailResponse] = {}
        for book_obj, job_obj in rows:
            if book_obj.id not in books_map:
                books_map[book_obj.id] = BookDetailResponse(
                    id=book_obj.id,
                    original_name=book_obj.original_name,
                    created_at=book_obj.created_at,
                    updated_at=book_obj.updated_at,
                )

            if job_obj:
                books_map[book_obj.id].add_job(job_obj)

        return PaginatedResponse(
            data=list(books_map.values()),
            meta=PaginationMeta(total=total_count, limit=limit, offset=offset),
        )
