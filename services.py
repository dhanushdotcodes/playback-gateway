import itertools
import time

from fastapi import HTTPException

from models.session_model import Session, SessionCreate

# In-memory store for now; swap for a real DB later.
_sessions: dict[int, Session] = {}
_next_id = itertools.count(1)


def _get(user_id: int, session_id: int) -> Session:
    session = _sessions.get(session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def play(user_id: int, data: SessionCreate) -> Session:
    """
    Create a play session for the user. This will create a new session and return it.
    """
    session = Session(
        session_id=next(_next_id),
        user_id=user_id,
        timestamp=int(time.time()),
        device_id=data.device_id,
        status="active",
        song_id=data.song_id,
    )
    _sessions[session.session_id] = session
    return session


def pause(user_id: int, session_id: int) -> Session:
    """
    Pause the session. This will update the session status to "paused".
    """
    session = _get(user_id, session_id)
    if session.status != "active":
        raise HTTPException(status_code=409, detail=f"Cannot pause a {session.status} session")
    session.status = "paused"
    return session


def expire(user_id: int, session_id: int) -> Session:
    """
    Expire the session. This will update the session status to "expired".
    """
    session = _get(user_id, session_id)
    if session.status == "expired":
        raise HTTPException(status_code=409, detail="Session already expired")
    session.status = "expired"
    return session
