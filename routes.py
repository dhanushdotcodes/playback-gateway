from fastapi import APIRouter, Depends, Request
from models.session_model import Session, SessionCreate, SessionRef
from services import play, pause, expire

router = APIRouter()

def current_user_id(request: Request) -> int:
    # Set by the authentication middleware in main.py.
    return request.state.user_id

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
