from __future__ import annotations

from fastapi import APIRouter, WebSocket
import asyncio
from datetime import datetime

router = APIRouter()


@router.websocket('/ws/realtime')
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({"event": "heartbeat", "ts": datetime.utcnow().isoformat()})
            await asyncio.sleep(2)
    except Exception:
        await ws.close()
