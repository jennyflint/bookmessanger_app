from enum import StrEnum


class ExportBookStatusEnum(StrEnum):
    NEW = "new"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REMOVED = "removed"
