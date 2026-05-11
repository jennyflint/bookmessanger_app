from typing import Annotated, cast
from urllib.parse import urlencode

from authx import TokenPayload
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth_provider.oauth_provider import oauth
from src.database import get_db
from src.exceptions.auth_exception import EmailAuthError
from src.exceptions.user_exception import UserInactiveError
from src.schema.response.auth_response import TokenResponse
from src.schema.response.error_response import ErrorResponse
from src.security import auth
from src.services.auth_service import AuthService
from src.settings.settings import auth_settings


router = APIRouter(prefix="/auth")


@router.get("/login-via-google")
async def login_via_google(
    request: Request,
    redirect_url: str | None = None,
    fallback_url: str | None = None,
) -> RedirectResponse:

    response = await oauth.google.authorize_redirect(
        request, auth_settings.redirect_oauth_uri
    )

    response = cast(RedirectResponse, response)
    if redirect_url:
        response.set_cookie(
            key="oauth_redirect_to",
            value=redirect_url,
            max_age=300,
            httponly=True,
            secure=True,
            samesite="lax",
        )
    if fallback_url:
        response.set_cookie(
            key="oauth_fallback_url",
            value=fallback_url,
            max_age=300,
            httponly=True,
            secure=True,
            samesite="lax",
        )

    return response


@router.get("/callback", response_model=None)
async def google_callback(
    request: Request, response: Response, db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse | ErrorResponse | RedirectResponse:
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    fallback_redirect_url = request.cookies.get("oauth_fallback_url")
    if not user_info:
        if fallback_redirect_url:
            error_query = urlencode({"error": "USER_INFO_NOT_FOUND"})
            return RedirectResponse(url=f"{fallback_redirect_url}?{error_query}")
        else:
            return ErrorResponse(
                error="USER_INFO_NOT_FOUND", type="USER_INFO_NOT_FOUND"
            )

    try:
        tokens = await AuthService.generate_authx_tokens(db, user_info)
    except EmailAuthError:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        if fallback_redirect_url:
            error_query = urlencode({"error": "EMAIL_AUTH_REQUIRED"})
            return RedirectResponse(url=f"{fallback_redirect_url}?{error_query}")
        else:
            return ErrorResponse(
                error="EMAIL_AUTH_REQUIRED", type="EMAIL_AUTH_REQUIRED"
            )
    except UserInactiveError as e:
        response.status_code = status.HTTP_403_FORBIDDEN
        if fallback_redirect_url:
            error_query = urlencode({"error": "USER_INACTIVE"})
            return RedirectResponse(url=f"{fallback_redirect_url}?{error_query}")
        else:
            return ErrorResponse(error=str(e), type="USER_INACTIVE")

    saved_redirect_url = request.cookies.get("oauth_redirect_to")

    if saved_redirect_url:
        redirect_response = RedirectResponse(url=f"{saved_redirect_url}")

        redirect_response.set_cookie(
            key="access_token",
            value=tokens.access_token,
            max_age=auth_settings.access_token_expire_minutes * 60,
            secure=True,
            samesite="lax",
            httponly=False,
        )
        if tokens.refresh_token:
            redirect_response.set_cookie(
                key="refresh_token",
                value=tokens.refresh_token,
                max_age=auth_settings.refresh_token_expire_days * 24 * 60 * 60,
                secure=True,
                samesite="lax",
                httponly=False,
            )

        redirect_response.set_cookie(
            key="user_email",
            value=user_info.get("email"),
            max_age=auth_settings.refresh_token_expire_days * 24 * 60 * 60,
            secure=True,
            samesite="lax",
            httponly=False,
        )

        redirect_response.delete_cookie(key="oauth_redirect_to")
        redirect_response.delete_cookie(key="oauth_fallback_url")

        return redirect_response
    else:
        return tokens


@router.post("/refresh/token")
def refresh_token(
    payload: Annotated[TokenPayload, Depends(auth.refresh_token_required)],
) -> TokenResponse:
    new_access_token = auth.create_access_token(uid=payload.sub)
    return TokenResponse(access_token=new_access_token, refresh_token=None)
