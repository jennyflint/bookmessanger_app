from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies import (
    get_enum_options,
)
from src.enums.enums import TemplateTypeEnum
from src.schema.response.enum_response import EnumOptionResponse


router = APIRouter()

TemplateOptionsDep = Annotated[
    list[EnumOptionResponse], Depends(lambda: get_enum_options(TemplateTypeEnum))
]


@router.get("/list")
async def get_template_list(options: TemplateOptionsDep) -> list[EnumOptionResponse]:
    return options
