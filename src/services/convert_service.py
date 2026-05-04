from src.enums.enums import FormatTypeEnum
from src.exceptions.convert_exception import ConvertFormatNotImplementedError
from src.services.converters.convert import IConverter


class ConvertService:
    def __init__(self) -> None:
        self._converters: dict[FormatTypeEnum, IConverter] = {}

    def register(self, format_type: FormatTypeEnum, converter: IConverter) -> None:
        self._converters[format_type] = converter

    def convert(
        self, content: str, file_path: str, format_type: FormatTypeEnum
    ) -> bool:
        converter = self._converters.get(format_type)

        if not converter:
            raise ConvertFormatNotImplementedError()

        return converter.convert(content, file_path)
