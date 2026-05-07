import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import redis
from sqlalchemy import Select, select
from sqlalchemy.orm import Mapper, Session, class_mapper

from src.database import Base, SessionLocal
from src.exceptions.job_exception import JobNotFoundError, JobObjectTableNotFoundError
from src.models.job import Job, JobStatusEnum
from src.settings.settings import app_settings


@dataclass
class TaskResult:
    message: str
    channel: str | None = None
    ws_data: dict[str, Any] | None = None


class JobCeleryService:
    def __init__(self, job_id: int, is_publish: bool = False) -> None:
        self.job_id = job_id
        self.is_publish = is_publish

        self.redis_client: redis.Redis | None = None

        if self.is_publish:
            self._create_redis_client()

    def _create_redis_client(self) -> None:
        self.redis_client = redis.Redis.from_url(app_settings.redis_url)

    def _redis_publish(self, channel: str, ws_data: dict[str, Any]) -> None:
        if self.redis_client and channel:
            self.redis_client.publish(channel, json.dumps(ws_data))

    def _get_job_by_id(self, db: Session, job_id: int) -> Job | None:
        stmt: Select[tuple[Job]] = select(Job).where(Job.id == job_id)
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def _get_target_entity(
        self, db: Session, object_table: str, object_id: int
    ) -> Any | None:
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
        return result.scalar_one_or_none()

    def _get_model_by_table_name(self, table_name: str) -> type[Any] | None:
        for mapper_obj in Base.registry.mappers:
            if getattr(mapper_obj.local_table, "name", None) == table_name:
                return mapper_obj.class_
        return None

    def main(
        self,
        celery_task: Callable[..., TaskResult],
        **kwargs: Any,
    ) -> str:
        with SessionLocal() as db:
            job = self._get_job_by_id(db, self.job_id)
            if not job:
                raise JobNotFoundError(self.job_id)

            job.status = JobStatusEnum.PROCESSING
            db.commit()

            target_object = self._get_target_entity(db, job.object_table, job.object_id)
            if not target_object:
                raise JobObjectTableNotFoundError(job.object_table, job.object_id)

            res_message = ""
            try:
                task_result: TaskResult = celery_task(db, job, target_object, **kwargs)
                res_message = task_result.message
                job.status = JobStatusEnum.COMPLETED
                db.commit()

                if self.is_publish and task_result.channel and task_result.ws_data:
                    self._redis_publish(task_result.channel, task_result.ws_data)

            except Exception as e:
                db.rollback()

                job.status = JobStatusEnum.FAILED
                db.commit()
                res_message = f"Failed to process job {self.job_id}: Error -> {e!s}"

            return res_message
