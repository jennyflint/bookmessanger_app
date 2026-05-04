from time import time

from src.config.book import STORAGE_COMPLETE_BOOK
from src.dependencies import (
    get_converter_service,
)
from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.models.book import Book
from src.services.html_data_injector_service import HtmlDataInjectorService
from src.utils.storage import Storage


class ConvertBookService:
    def __init__(
        self, book: Book, format_type: FormatTypeEnum, template: TemplateTypeEnum
    ):
        self.convert_service = get_converter_service()
        self.book = book
        self.user = book.user
        self.format_type = format_type
        self.template = template

    def _get_book_json_model(self) -> str:
        return Storage.get_book_model_by_book(self.book)

    def _get_html_template(self) -> str:
        return Storage.get_template_by_type(self.template)

    def main(self) -> str:
        html_template = self._get_html_template()
        json_model = self._get_book_json_model()
        html_data_injector_service = HtmlDataInjectorService(
            html_content=html_template, json_data=json_model
        )
        html_page = html_data_injector_service.main()

        path_to_complete_file = f"{STORAGE_COMPLETE_BOOK}/{self.user.id}/{self.book.id}"
        filename = f"{int(time())}_{self.book.id}.{self.format_type}"
        self.convert_service.convert(
            content=html_page,
            format_type=self.format_type,
            file_path=f"{path_to_complete_file}/{filename}",
        )

        return filename
