import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.requests import HTTPConnection
from models.session_model import Session, SessionCreate, SessionRef
from services import HEARTBEAT_TIMEOUT, play, pause, expire, heartbeat

router = APIRouter()

def current_user_id(conn: HTTPConnection) -> int:
    # Set by the authentication middleware in main.py.
    return conn.state.user_id

@router.post("/play", response_model=Session)
async def play_song(data: SessionCreate, user_id: int = Depends(current_user_id)):
    """
    Create a play session for the user. This will create a new session and return it.
    """
    return play(user_id, data)

@router.post("/pause", response_model=Session)
async def pause_song(ref: SessionRef, user_id: int = Depends(current_user_id)):
    """
    Pause the session. This will update the session status to "paused".
    """
    return pause(user_id, ref.session_id)

@router.post("/expire", response_model=Session)
async def expire_session(ref: SessionRef, user_id: int = Depends(current_user_id)):
    """
    Expire the session. This will update the session status to "expired".
    """
    return expire(user_id, ref.session_id)


# Clients send a heartbeat every HEARTBEAT_INTERVAL seconds; no heartbeat for
# HEARTBEAT_TIMEOUT seconds and the session is expired.
HEARTBEAT_INTERVAL = 5

@router.websocket("/ws/{session_id}")
async def session_heartbeat(ws: WebSocket, session_id: int, user_id: int = Depends(current_user_id)):
    """
    Open this after /play. Send any text message (e.g. "heartbeat") every 5 seconds.
    If nothing arrives for 15 seconds, or the socket closes, the session is expired.
    """
    try:
        session = heartbeat(user_id, session_id)
    except HTTPException:
        await ws.close(code=4404)  # no such session for this user
        return
    if session.status == "expired":
        await ws.close(code=4409)
        return

    await ws.accept()
    try:
        while True:
            await asyncio.wait_for(ws.receive_text(), timeout=HEARTBEAT_TIMEOUT)
            if heartbeat(user_id, session_id).status == "expired":
                await ws.close(code=4001, reason="session expired")
                return
    except asyncio.TimeoutError:
        _expire_quietly(user_id, session_id)
        await ws.close(code=4000, reason="heartbeat timeout")
    except WebSocketDisconnect:
        _expire_quietly(user_id, session_id)


def _expire_quietly(user_id: int, session_id: int) -> None:
    try:
        expire(user_id, session_id)
    except HTTPException:
        pass  # already expired or gone
