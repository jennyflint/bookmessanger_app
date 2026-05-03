from src.exceptions.convert_exceptions import ConvertFormatNotImplementedError
from src.services.converters.convert import FormatType, IConverter


class ConvertService:
    def __init__(self) -> None:
        self._converters: dict[FormatType, IConverter] = {}

    def register(self, format_type: FormatType, converter: IConverter) -> None:
        self._converters[format_type] = converter

    def convert(self, content: str, file_path: str, format_type: FormatType) -> bool:
        converter = self._converters.get(format_type)

        if not converter:
            raise ConvertFormatNotImplementedError()

        return converter.convert(content, file_path)
