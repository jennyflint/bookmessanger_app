import os
from typing import Annotated, Any

import jwt
from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.file_service import FileService
from validators.file_validator import FileValidator


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "")

if not JWT_SECRET:
    err_msg = "JWT_SECRET_KEY environment variable is not set"
    raise ValueError(err_msg)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        user_id = int(user_id_str)

    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired"
        ) from err
    except (jwt.InvalidTokenError, ValueError) as err:
        raise credentials_exception from err

    query = select(User).where(User.id == user_id, User.is_active)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


def get_file_service() -> FileService:
    return FileService()


# validator dependency


def file_validator_dependency(
    *,
    allowed_extensions: set[str] | None = None,
    allowed_content_types: set[str] | None = None,
    max_size: int | str | None = None,
) -> Any:
    validator = FileValidator(
        allowed_extensions=allowed_extensions,
        allowed_content_types=allowed_content_types,
        max_size=max_size,
    )

    async def _validate(file: Annotated[UploadFile, File()]) -> UploadFile:
        return await validator.validate(file)

    return Depends(_validate)
