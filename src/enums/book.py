from enum import StrEnum


class BookActionStatusEnum(StrEnum):
    NEW = "new"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REMOVED = "removed"
