import os

from dotenv import load_dotenv
from pydantic import BaseModel, HttpUrl, field_validator

from src.enums.enums import FormatTypeEnum, TemplateTypeEnum


load_dotenv()
APP_URL = os.getenv("APP_URL", "")


class Character(BaseModel):
    id: int
    avatar: HttpUrl

    @field_validator("avatar")
    @classmethod
    def validate_avatar_domain(cls, value: HttpUrl) -> HttpUrl:
        url_str = str(value)

        if not url_str.startswith(APP_URL):
            err_msg = (
                f"URL avatar must belong to the domain {APP_URL}, but got {url_str}"
            )
            raise ValueError(err_msg)

        return value


class ConvertBookRequest(BaseModel):
    template: TemplateTypeEnum
    format: FormatTypeEnum
    characters: list[Character]
