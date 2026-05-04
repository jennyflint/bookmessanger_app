from pydantic import BaseModel

from src.enums.enums import FormatTypeEnum, TemplateTypeEnum


class ConvertBookRequest(BaseModel):
    template: TemplateTypeEnum
    format: FormatTypeEnum
