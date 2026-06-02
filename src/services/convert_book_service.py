from time import time

from src.enums.enums import FormatTypeEnum, TemplateTypeEnum
from src.models.book import Book
from src.services.convert_service import ConvertService
from src.services.converters.convert import PdfConverter
from src.services.html_data_injector_service import HtmlDataInjectorService
from src.services.module.playwright_pdf_module import PlaywrightPDFGenerator
from src.settings.settings import app_settings, book_settings
from src.utils.storage import Storage


def get_converter_service() -> ConvertService:
    playwright_gen = PlaywrightPDFGenerator(app_settings.playwright_ws_endpoint)
    pdf_converter = PdfConverter(playwright_gen)
    service = ConvertService()
    service.register(FormatTypeEnum.PDF, pdf_converter)

    return service


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

    def main(self) -> str:
        json_model = self._get_book_json_model()

        html_data_injector_service = HtmlDataInjectorService(
            template=self.template, json_data=json_model
        )
        html_page = html_data_injector_service.main()

        path_to_export_file = (
            f"{book_settings.storage_export_book}/{self.user.id}/{self.book.id}"
        )
        filename = f"{int(time())}_{self.book.id}.{self.format_type}"
        self.convert_service.convert(
            content=html_page,
            format_type=self.format_type,
            file_path=f"{path_to_export_file}/{filename}",
        )

        return filename
