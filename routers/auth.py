import os
from typing import Annotated, Any, cast

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth_provider.oauth_provider import oauth
from database import get_db
from services.auth_service import AuthService


load_dotenv()
app = FastAPI()

router = APIRouter(prefix="/auth")

REDIRECT_URI = os.getenv("REDIRECT_OAUTH_URI")
if not REDIRECT_URI:
    err_msg = "REDIRECT_OAUTH_URI is not set in the environment variables"
    raise ValueError(err_msg)


@router.get("/login-via-google")
async def login_via_google(request: Request) -> RedirectResponse:
    redirect_uri = REDIRECT_URI
    response = await oauth.google.authorize_redirect(request, redirect_uri)

    return cast(RedirectResponse, response)


@router.get("/callback")
async def google_callback(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    auth_service = AuthService(db)
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    app_tokens = await auth_service.process_google_user(user_info)

    return app_tokens


@app.post("/auth/refresh")
async def refresh_token(
    refresh_token: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    auth_service = AuthService(db)
    tokens = await auth_service.rotate_refresh_token(refresh_token)
    return tokens
