import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket
from redis.asyncio import Redis
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)

from src.settings.settings import app_settings


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        async with self.lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        async with self.lock:
            connections = self.active_connections.get(user_id)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                self.active_connections.pop(user_id, None)

    async def send_personal_message(
        self,
        message: dict[str, Any],
        user_id: int,
    ) -> None:
        async with self.lock:
            connections = self.active_connections.get(user_id, set()).copy()

        if not connections:
            return

        dead_connections: list[WebSocket] = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        if dead_connections:
            async with self.lock:
                current_connections = self.active_connections.get(user_id)
                if current_connections:
                    for websocket in dead_connections:
                        current_connections.discard(websocket)
                    if not current_connections:
                        self.active_connections.pop(user_id, None)

    async def disconnect_all(self) -> None:
        async with self.lock:
            self.active_connections.clear()


ws_manager = ConnectionManager()


async def redis_listener(redis: Redis) -> None:
    while True:
        pubsub = None

        try:
            pubsub = redis.pubsub(ignore_subscribe_messages=True)
            await pubsub.psubscribe("user_notifications_*")

            logger.info("Redis pubsub listener started")

            async for message in pubsub.listen():
                if message.get("type") != "pmessage":
                    continue

                try:
                    channel = message["channel"].decode()
                    user_id = int(channel.rsplit("_", 1)[1])
                    payload = json.loads(message["data"].decode())

                    await ws_manager.send_personal_message(
                        payload,
                        user_id,
                    )
                except Exception:
                    logger.exception("Failed to process redis message payload")

        except asyncio.CancelledError:
            logger.info("Redis listener stopped")
            raise

        except RedisTimeoutError:
            logger.debug("Redis pubsub idle timeout. Re-subscribing instantly...")
            continue

        except RedisConnectionError:
            logger.warning("Redis connection lost. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

        except Exception:
            logger.exception(
                "Redis listener crashed unexpectedly. Reconnecting in 5 seconds..."
            )
            await asyncio.sleep(5)

        finally:
            if pubsub:
                try:
                    await pubsub.aclose()  # type: ignore[no-untyped-call]
                except Exception as e:
                    logger.debug("Failed to cleanly close pubsub: %s", e)


redis_listener_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global redis_listener_task

    redis = Redis.from_url(
        app_settings.redis_url,
        decode_responses=False,
        health_check_interval=20,
        socket_timeout=None,
        socket_connect_timeout=5,
    )

    app.state.redis = redis
    redis_listener_task = asyncio.create_task(redis_listener(redis))

    try:
        yield
    finally:
        if redis_listener_task:
            redis_listener_task.cancel()
            try:
                await redis_listener_task
            except asyncio.CancelledError as e:
                logger.info("Redis listener task cancelled: %s", e)

        await redis.aclose()
        await ws_manager.disconnect_all()
