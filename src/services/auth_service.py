from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.auth import REFRESH_TOKEN_EXPIRE_DAYS
from src.exceptions.auth_exception import EmailAuthError
from src.exceptions.user_exception import UserInactiveError
from src.models.user import RefreshToken, User
from src.schema.response.auth_response import TokenResponse
from src.security import auth


class AuthService:
    @staticmethod
    async def get_or_create_user(db: AsyncSession, email: str) -> User:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(email=email)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    @staticmethod
    async def save_refresh_token(db: AsyncSession, user_id: int, token: str) -> None:
        expires_date = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        db_refresh_token = RefreshToken(
            user_id=user_id, token=token, expires_at=expires_date, is_revoked=False
        )
        db.add(db_refresh_token)
        await db.commit()

    @classmethod
    async def generate_authx_tokens(
        cls, db: AsyncSession, user_info: dict[str, str]
    ) -> TokenResponse:
        email = user_info.get("email")

        if not email:
            raise EmailAuthError()

        user = await cls.get_or_create_user(db, email)

        if not user.is_active:
            raise UserInactiveError()

        uid_str = str(user.id)

        # Generate tokens
        access_token = auth.create_access_token(uid=uid_str)
        refresh_token = auth.create_refresh_token(uid=uid_str)

        # Save refresh_token in the database
        await cls.save_refresh_token(db, user.id, refresh_token)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
