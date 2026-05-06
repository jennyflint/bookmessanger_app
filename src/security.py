from datetime import timedelta
from typing import Any

from authx import AuthX, AuthXConfig

from src.settings.settings import auth_settings


authx_config = AuthXConfig(
    JWT_SECRET_KEY=auth_settings.jwt_secret_key,
    JWT_ALGORITHM=auth_settings.jwt_algorithm,
    JWT_TOKEN_LOCATION=["headers"],
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(
        minutes=auth_settings.access_token_expire_minutes
    ),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=auth_settings.refresh_token_expire_days),
)

auth: AuthX[Any] = AuthX(config=authx_config)
