import warnings
from pathlib import Path
from typing import Annotated, Literal

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub
from pydantic import BaseModel, Field, TypeAdapter


warnings.filterwarnings(action="ignore", category=UserWarning)


class FB2Converter(BaseModel):
    format: Literal[".fb2"]
    path_to_file: str

    def convert(self) -> list[str]:
        with Path(self.path_to_file).open(encoding="utf-8") as file:
            xml_content = file.read()
        soup = BeautifulSoup(xml_content, "lxml-xml")
        bodies = soup.find_all("body")

        lines = []
        for body in bodies:
            for element in body.find_all(["p", "title", "subtitle", "v"]):
                text = element.get_text(strip=True)
                if text:
                    lines.append(text)
        return lines


class EPUBConverter(BaseModel):
    format: Literal[".epub"]
    path_to_file: str

    def convert(self) -> list[str]:
        book = epub.read_epub(self.path_to_file)
        lines = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                html_content = item.get_content()
                soup = BeautifulSoup(html_content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                if text:
                    lines.append(text)
                    lines.append("\n" + "=" * 40 + "\n")
        return lines


AnyConverter = Annotated[FB2Converter | EPUBConverter, Field(discriminator="format")]

converter_factory: TypeAdapter[AnyConverter] = TypeAdapter(AnyConverter)
