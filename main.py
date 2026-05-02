import os

from fastapi import APIRouter, Depends, FastAPI
from starlette.middleware.sessions import SessionMiddleware

from config.auth import SESSION_SECRET_KEY
from dependencies import get_current_user
from routers.auth import router as auth_router
from routers.book import router as book_router
from security import auth


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

auth.handle_errors(app)

api_router = APIRouter(prefix="/api/v1")
auth.handle_errors(app)
api_router.include_router(auth_router)
api_router.include_router(
    book_router, prefix="/book", dependencies=[Depends(get_current_user)]
)
app.include_router(api_router)


@app.get("/")
def read_root() -> dict[str, str]:
    db_url = os.getenv("DATABASE_URL", "URL not found")
    return {"message": "FastAPI is running!", "db_url": db_url}
