from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.websockets.manager import ws_manager


router = APIRouter()


@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
