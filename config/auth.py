import os
from typing import Literal, cast


AlgorithmType = Literal[
    "HS256",
    "HS384",
    "HS512",
    "ES256",
    "ES256K",
    "ES384",
    "ES512",
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
]


GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
REDIRECT_OAUTH_URI: str = os.getenv("REDIRECT_OAUTH_URI", "")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))
JWT_ALGORITHM: AlgorithmType = cast(AlgorithmType, os.getenv("JWT_ALGORITHM", "HS256"))
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "")
