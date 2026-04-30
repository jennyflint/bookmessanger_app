import os

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from routers.auth import router as auth_router


load_dotenv()

app = FastAPI()
SESSION_SECRET = os.getenv("JWT_SECRET_KEY", "super-secret-session-key")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.include_router(auth_router)


@app.get("/")
def read_root() -> dict[str, str]:
    db_url = os.getenv("DATABASE_URL", "URL not found")
    return {"message": "FastAPI is running!", "db_url": db_url}
