import os

from celery import Celery
from dotenv import load_dotenv


load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.tasks.parsing_book_task", "src.tasks.convert_book_task"],
)

celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.broker_transport_options = {
    "retry_on_timeout": True,
    "interval_start": 0,
    "interval_step": 0.5,
    "interval_max": 5,
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
