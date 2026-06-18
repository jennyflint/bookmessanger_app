import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

import redis
from sqlalchemy import Select, select
from sqlalchemy.orm import Mapper, Session, class_mapper

from src.database import SessionLocal
from src.exceptions.job_exception import JobNotFoundError, JobObjectTableNotFoundError
from src.models.base import Base
from src.models.job import Job, JobStatusEnum
from src.settings.settings import app_settings


T = TypeVar("T")
logger = logging.getLogger(__name__)


class JobCeleryService:
    job: Job

    def __init__(
        self, job_id: int, is_publish: bool = False, is_callback: bool = False
    ) -> None:
        self.job_id = job_id
        self.is_publish = is_publish
        self.is_callback = is_callback
        self._create_initial()
        self.redis_client: redis.Redis | None = None
        self.channel: str | None = None
        self.ws_data: dict[str, Any] | None = None

        if self.is_publish:
            self._create_redis_client()

    def _create_initial(self) -> None:
        with SessionLocal() as db:
            self._find_job_by_id(db)
            self._find_target_entity(db, self.job.object_table, self.job.object_id)

    def add_websocket_channel(self, channel: str, ws_data: dict[str, Any]) -> None:
        self.channel = channel
        self.ws_data = ws_data

    def _create_redis_client(self) -> None:
        self.redis_client = redis.Redis.from_url(app_settings.redis_url)

    def _redis_publish(self, channel: str, ws_data: dict[str, Any]) -> None:
        if self.redis_client and channel:
            self.redis_client.publish(channel, json.dumps(ws_data))

    def _find_job_by_id(self, db: Session) -> None:
        stmt: Select[tuple[Job]] = select(Job).where(Job.id == self.job_id)
        result = db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise JobNotFoundError(self.job_id)
        self.job = job

    def _find_target_entity(
        self, db: Session, object_table: str, object_id: int
    ) -> None:
        target_model = self._get_model_by_table_name(object_table)

        if not target_model:
            err_msg = f"Model for table '{object_table}' not found in Base.registry"
            raise ValueError(err_msg)

        mapper: Mapper[Any] = class_mapper(target_model)
        primary_key_column = mapper.primary_key[0]
        stmt: Select[tuple[Any]] = select(target_model).where(
            primary_key_column == object_id
        )

        result = db.execute(stmt)
        self.target_object = result.scalar_one_or_none()

    def _get_model_by_table_name(self, table_name: str) -> type[Any] | None:
        for mapper_obj in Base.registry.mappers:
            if getattr(mapper_obj.local_table, "name", None) == table_name:
                return mapper_obj.class_
        return None

    def _update_job_status(self, db: Session, job: Job, status: JobStatusEnum) -> None:
        job.status = status
        db.commit()

        if self.is_publish and self.channel and self.ws_data:
            clone_ws_data = self.ws_data.copy()
            clone_ws_data["status"] = status.value

            self._redis_publish(self.channel, clone_ws_data)

    def get_target_object_after_verify(self, expected_type: type[T]) -> T:
        obj = self.target_object
        if not isinstance(obj, expected_type):
            err_msg = (
                f"Expected object to be of type {expected_type.__name__}, "
                f"got {type(obj).__name__}"
            )
            raise TypeError(err_msg)
        return obj

    def get_job(self) -> Job | None:
        return self.job

    def main(
        self,
        celery_task: Callable[..., bool],
        **kwargs: Any,
    ) -> str:
        with SessionLocal() as db:
            job = db.merge(self.job)
            self._update_job_status(db, job, JobStatusEnum.PROCESSING)

            if not self.target_object:
                raise JobObjectTableNotFoundError(job.object_table, job.object_id)

            res_message = ""
            try:
                is_success = celery_task(db, **kwargs)

                if not self.is_callback or not is_success:
                    self._update_job_status(
                        db,
                        job,
                        JobStatusEnum.COMPLETED if is_success else JobStatusEnum.FAILED,
                    )
            except Exception as e:
                db.rollback()

                self._update_job_status(db, job, JobStatusEnum.FAILED)
                res_message = f"Failed to process job {self.job_id}: Error -> {e!s}"

                logger.exception(res_message)

            return res_message
