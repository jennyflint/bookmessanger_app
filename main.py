import os

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.dependencies import get_current_user, get_current_user_from_websocket
from src.routers.auth import router as auth_router
from src.routers.book import router as book_router
from src.routers.template import router as template_router
from src.routers.websockets import router as websocket_router
from src.security import auth
from src.settings.settings import app_settings, auth_settings
from src.websockets.manager import lifespan


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=auth_settings.session_secret_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origin_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth.handle_errors(app)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(
    book_router, prefix="/book", dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    template_router, prefix="/template", dependencies=[Depends(get_current_user)]
)

app.include_router(
    websocket_router,
    prefix="/ws",
    dependencies=[Depends(get_current_user_from_websocket)],
)
app.include_router(api_router)


@app.get("/")
def read_root() -> dict[str, str]:
    db_url = os.getenv("DATABASE_URL", "URL not found")
    return {"message": "FastAPI is running!", "db_url": db_url}
