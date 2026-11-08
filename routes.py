from fastapi import APIRouter, Header
from models.session_model import Session, SessionCreate, SessionRef
from services import play, pause, expire

router = APIRouter()

# TODO: replace the X-User-Id header with real auth.

@router.post("/play", response_model=Session)
async def play_song(data: SessionCreate, user_id: int = Header(alias="X-User-Id")):
    """
    Create a play session for the user. This will create a new session and return it.
    """
    return play(user_id, data)

@router.post("/pause", response_model=Session)
async def pause_song(ref: SessionRef, user_id: int = Header(alias="X-User-Id")):
    """
    Pause the session. This will update the session status to "paused".
    """
    return pause(user_id, ref.session_id)

@router.post("/expire", response_model=Session)
async def expire_session(ref: SessionRef, user_id: int = Header(alias="X-User-Id")):
    """
    Expire the session. This will update the session status to "expired".
    """
    return expire(user_id, ref.session_id)
