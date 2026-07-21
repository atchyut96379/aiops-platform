import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.database import SessionLocal
from app.services.live_monitoring import LiveMonitoringService
from app.repositories.user import UserRepository

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/live-metrics")
async def live_metrics_ws(
    websocket: WebSocket,
    token: str = Query(...),
    interval: int = Query(5, ge=2, le=60),
) -> None:
    await websocket.accept()
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4401)
            return
        user_id = int(payload["sub"])
        org_id = payload.get("org_id")
        if org_id is None:
            await websocket.close(code=4403)
            return
    except Exception:
        await websocket.close(code=4401)
        return

    try:
        while True:
            db = SessionLocal()
            try:
                user = UserRepository(db).get(user_id)
                if user is None or not user.is_active:
                    await websocket.close(code=4401)
                    return
                snapshot = LiveMonitoringService(db).get_live_snapshot(
                    organization_id=int(org_id),
                    requester=user,
                    minutes=15,
                )
            finally:
                db.close()
            await websocket.send_text(json.dumps(snapshot, default=str))
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        return
