import os
from datetime import UTC, datetime, timedelta
from typing import Any

from authlib.jose import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import RefreshToken, User


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,  # 64 MB
    argon2__parallelism=2,
)

ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

if not ACCESS_TOKEN_EXPIRES_MINUTES or not REFRESH_TOKEN_EXPIRES_DAYS:
    err_msg = "Token expiration environment variables are not set"
    raise ValueError(err_msg)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")

        if not self.jwt_secret:
            err_msg = "JWT_SECRET_KEY environment variable is not set"
            raise ValueError(err_msg)

    async def process_google_user(
        self, user_info: dict[str, Any]
    ) -> dict[str, str | datetime]:
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google response missing email")

        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            user = User(email=email)
            self.db.add(user)

            await self.db.flush()

        tokens = self._generate_app_tokens(str(user.id))
        db_token = RefreshToken(
            user_id=user.id,
            token=pwd_context.hash(tokens["refresh_token"]),
            expires_at=tokens["refresh_exp_date"],
        )
        self.db.add(db_token)
        await self.db.commit()
        tokens.pop("refresh_exp_date", None)
        return tokens

    def _generate_app_tokens(self, subject: str) -> dict[str, str | datetime]:
        now = datetime.now(UTC)
        access_exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
        refresh_exp = now + timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)

        header = {"alg": "HS256"}

        access_token = jwt.encode(
            header,
            {"sub": subject, "exp": access_exp, "type": "access"},
            self.jwt_secret,
        )

        refresh_token = jwt.encode(
            header,
            {"sub": subject, "exp": refresh_exp, "type": "refresh"},
            self.jwt_secret,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "refresh_exp_date": refresh_exp,
            "token_type": "bearer",
        }

    async def rotate_refresh_token(
        self, plain_refresh_token: str
    ) -> dict[str, str | datetime]:
        try:
            payload = jwt.decode(
                plain_refresh_token, self.jwt_secret, algorithms=["HS256"]
            )
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")

            user_id = int(payload["sub"])

        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=401, detail="Refresh token expired"
            ) from err

        except jwt.InvalidTokenError as err:
            raise HTTPException(
                status_code=401, detail="Invalid refresh token format"
            ) from err

        except ValueError as err:
            raise HTTPException(
                status_code=401, detail="Invalid subject in token"
            ) from err

        query = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await self.db.execute(query)
        db_tokens = result.scalars().all()

        matched_token = None
        for dt in db_tokens:
            if pwd_context.verify(plain_refresh_token, dt.token):
                matched_token = dt
                break

        if not matched_token:
            raise HTTPException(
                status_code=401, detail="Refresh token not found in database"
            )

        if matched_token.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=401, detail="Refresh token expired in database"
            )

        if matched_token.is_revoked:
            await self._revoke_all_user_tokens(user_id)
            raise HTTPException(
                status_code=401,
                detail="Token compromise detected. All sessions revoked.",
            )

        matched_token.is_revoked = True
        new_tokens = self._generate_app_tokens(str(user_id))

        new_db_token = RefreshToken(
            user_id=user_id,
            token=pwd_context.hash(new_tokens["refresh_token"]),
            expires_at=new_tokens["refresh_exp_date"],
        )

        self.db.add(new_db_token)
        await self.db.commit()

        new_tokens.pop("refresh_exp_date", None)
        return new_tokens

    async def _revoke_all_user_tokens(self, user_id: int) -> None:
        query = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.execute(query)
        await self.db.commit()
