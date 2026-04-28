import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv()


def get_database_url() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    if not all([user, password, db_name]):
        missing = [
            k
            for k, v in {
                "POSTGRES_USER": user,
                "POSTGRES_PASSWORD": password,
                "POSTGRES_DB": db_name,
            }.items()
            if not v
        ]
        err_msg = f"Missing environment variables: {', '.join(missing)}"
        raise ValueError(err_msg)

    database_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return database_url


SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
