from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.dependencies import get_current_user_from_websocket
from src.models.user import User
from src.websockets.manager import ws_manager


router = APIRouter()


@router.websocket("/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    user: Annotated[User, Depends(get_current_user_from_websocket)],
) -> None:

    await ws_manager.connect(websocket, user.id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, user.id)
