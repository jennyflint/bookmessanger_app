from sqlalchemy.ext.asyncio import AsyncSession

from src.models.book import ExportBook


class ExportBookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, export_book_id: int) -> ExportBook | None:
        return await self.session.get(ExportBook, export_book_id)
