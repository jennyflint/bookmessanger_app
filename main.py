import logging
import os
from pathlib import Path

from authx.exceptions import AuthXException, JWTDecodeError
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.dependencies import get_current_user, get_current_user_from_websocket
from src.routers.auth import router as auth_router
from src.routers.avatar import router as avatar_router
from src.routers.book import router as book_router
from src.routers.template import router as template_router
from src.routers.websockets import router as websocket_router
from src.settings.settings import app_settings, auth_settings
from src.websockets.manager import lifespan


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOGS_DIR / "app.log",
    level=logging.ERROR,
    format=(
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(filename)s:%(lineno)d (%(funcName)s) | %(message)s"
    ),
    encoding="utf-8",
    force=True,
)

app = FastAPI(lifespan=lifespan)

AVATARS_DIR = Path("storage/characters/avatars")

AVATARS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/avatars", StaticFiles(directory=AVATARS_DIR), name="avatars")


@app.exception_handler(JWTDecodeError)
@app.exception_handler(AuthXException)
async def authx_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "message": "Invalid or expired token",
            "error_type": exc.__class__.__name__,
            "details": str(exc),
        },
    )


app.add_middleware(SessionMiddleware, secret_key=auth_settings.session_secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(
    book_router, prefix="/book", dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    template_router, prefix="/template", dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    avatar_router, prefix="/avatar", dependencies=[Depends(get_current_user)]
)

app.include_router(api_router)


app.include_router(
    websocket_router,
    prefix="/ws",
    dependencies=[Depends(get_current_user_from_websocket)],
)


@app.get("/")
def read_root() -> dict[str, str]:
    db_url = os.getenv("DATABASE_URL", "URL not found")
    return {"message": "FastAPI is running!", "db_url": db_url}
