from typing import Annotated, cast

from authx import TokenPayload
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth_provider.oauth_provider import oauth
from config.auth import REDIRECT_OAUTH_URI
from database import get_db
from exceptions.auth_exception import EmailAuthError
from exceptions.user_exception import UserInactiveError
from schema.response.auth_response import TokenResponse
from schema.response.error_response import ErrorResponse
from security import auth
from services.auth_service import AuthService


router = APIRouter(prefix="/auth")


@router.get("/login-via-google")
async def login_via_google(request: Request) -> RedirectResponse:
    response = await oauth.google.authorize_redirect(request, REDIRECT_OAUTH_URI)

    return cast(RedirectResponse, response)


@router.get("/callback")
async def google_callback(
    request: Request, response: Response, db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse | ErrorResponse:
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        return ErrorResponse(error="User info not found", type="USER_INFO_NOT_FOUND")

    try:
        tokens = await AuthService.generate_authx_tokens(db, user_info)
    except EmailAuthError as e:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return ErrorResponse(error=str(e), type="EMAIL_AUTH_REQUIRED")
    except UserInactiveError as e:
        response.status_code = status.HTTP_403_FORBIDDEN
        return ErrorResponse(error=str(e), type="USER_INACTIVE")

    return tokens


@router.post("/refresh/token")
def refresh_token(
    payload: Annotated[TokenPayload, Depends(auth.refresh_token_required)],
) -> TokenResponse:
    new_access_token = auth.create_access_token(uid=payload.sub)
    return TokenResponse(access_token=new_access_token, refresh_token=None)
