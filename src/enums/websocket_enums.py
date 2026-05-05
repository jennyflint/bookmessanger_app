from enum import StrEnum


class WebsocketStatusEnum(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class WebsocketTypeEnum(StrEnum):
    BOOK_CONVERTED = "book_converted"
    CREATE_BOOK_MODEL = "create_book_model"
