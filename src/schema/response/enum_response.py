from pydantic import BaseModel, Field


class EnumOptionResponse(BaseModel):
    value: str = Field(..., description="Value")
    label: str = Field(..., description="Label")

    class Config:
        frozen = True
