import json
from typing import Annotated, Any, cast
from urllib.parse import quote, urlencode

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
from src.settings.settings import app_settings, auth_settings


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

    response.delete_cookie(key="oauth_redirect_to")
    response.delete_cookie(key="oauth_fallback_url")

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

    fallback_redirect_url = request.cookies.get("oauth_fallback_url")
    response.delete_cookie(key="user_data")

    def handle_auth_error(
        error_code: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> ErrorResponse | RedirectResponse:
        response.status_code = status_code
        if fallback_redirect_url:
            error_query = urlencode({"error": error_code})
            return RedirectResponse(url=f"{fallback_redirect_url}?{error_query}")
        return ErrorResponse(error=error_code, type=error_code)

    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo", {})
    email = user_info.get("email")

    if not email:
        return handle_auth_error("USER_INFO_NOT_FOUND")

    try:
        user, access_token, refresh_token = await AuthService.generate_authx_tokens(
            db, user_info
        )
    except EmailAuthError:
        return handle_auth_error("EMAIL_AUTH_REQUIRED", status.HTTP_401_UNAUTHORIZED)
    except UserInactiveError as e:
        return handle_auth_error(
            str(e) if str(e) else "USER_INACTIVE", status.HTTP_403_FORBIDDEN
        )

    saved_redirect_url = request.cookies.get("oauth_redirect_to")
    if not saved_redirect_url:
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    redirect_response = RedirectResponse(url=saved_redirect_url)
    cookie_domain = app_settings.app_host

    base_cookie_kwargs: dict[str, Any] = {
        "secure": True,
        "samesite": "lax",
        "domain": cookie_domain,
        "httponly": False,
    }

    redirect_response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=auth_settings.access_token_expire_minutes * 60,
        **base_cookie_kwargs,
    )

    if refresh_token:
        refresh_max_age = auth_settings.refresh_token_expire_days * 24 * 60 * 60
        redirect_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_max_age,
            **base_cookie_kwargs,
        )

        user_data_str = json.dumps({"id": user.id, "email": user.email})
        redirect_response.set_cookie(
            key="user_data",
            value=quote(user_data_str),
            max_age=refresh_max_age,
            **base_cookie_kwargs,
        )

    redirect_response.delete_cookie(key="oauth_redirect_to")
    redirect_response.delete_cookie(key="oauth_fallback_url")

    return redirect_response


@router.post("/refresh/token")
def refresh_token(
    payload: Annotated[TokenPayload, Depends(auth.refresh_token_required)],
) -> TokenResponse:
    new_access_token = auth.create_access_token(uid=payload.sub)
    return TokenResponse(access_token=new_access_token, refresh_token=None)
