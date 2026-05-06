import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from redis.asyncio import Redis

from src.settings.settings import app_settings


redis_listener_task = None


async def redis_listener() -> None:
    redis = Redis.from_url(app_settings.redis_url)
    pubsub = redis.pubsub()
    await pubsub.psubscribe("user_notifications_*")

    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"].decode("utf-8")
                user_id = int(channel.split("_")[-1])

                data = json.loads(message["data"].decode("utf-8"))
                await ws_manager.send_personal_message(data, user_id)
    except asyncio.CancelledError:
        await pubsub.unsubscribe("user_notifications_*")
        await redis.aclose()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    global redis_listener_task
    redis_listener_task = asyncio.create_task(redis_listener())
    yield
    if redis_listener_task:
        redis_listener_task.cancel()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(
        self, message: dict[str, str], user_id: int
    ) -> None:
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)


ws_manager = ConnectionManager()
