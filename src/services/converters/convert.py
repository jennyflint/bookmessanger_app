from typing import Protocol

from src.services.module.playwright_pdf_module import PlaywrightPDFGenerator


class IConverter(Protocol):
    def convert(self, content: str, file_path: str) -> bool: ...


class PdfConverter(IConverter):
    def __init__(self, pdf_generator: PlaywrightPDFGenerator):
        self.pdf_generator = pdf_generator

    def convert(self, content: str, file_path: str) -> bool:
        return self.pdf_generator.save_pdf_to_file(content, file_path)
