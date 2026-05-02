from datetime import timedelta
from typing import Any

from authx import AuthX, AuthXConfig

from src.config.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


authx_config = AuthXConfig(
    JWT_SECRET_KEY=JWT_SECRET_KEY,
    JWT_ALGORITHM=JWT_ALGORITHM,
    JWT_TOKEN_LOCATION=["headers"],
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
)

auth: AuthX[Any] = AuthX(config=authx_config)
