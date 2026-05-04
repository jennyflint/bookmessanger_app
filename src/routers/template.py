from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import HTMLResponse

from src.config.book import STORAGE_HTML_TEMPLATE
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


@router.get("/code/{template_type}")
async def get_template_by_type(
    template_type: TemplateTypeEnum,
) -> HTMLResponse:

    file_name = f"{template_type}.html"
    template_path = STORAGE_HTML_TEMPLATE / file_name

    if not template_path.exists():
        raise HTTPException(
            status_code=404, detail=f"File {file_name} not found on the server"
        )

    try:
        html_content = template_path.read_text(encoding="utf-8")
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
