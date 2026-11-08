import json
import os
import random
import tempfile
import threading
import time
from pathlib import Path

from fastapi import HTTPException

from models.session_model import Session, SessionCreate

DB_PATH = Path(__file__).parent / "db.json"

# Handlers run in a threadpool; serialise read-modify-write cycles on the file.
_lock = threading.Lock()


def _load() -> dict:
    with DB_PATH.open() as f:
        return json.load(f)


def _save(db: dict) -> None:
    # Write to a temp file then rename so a crash can't leave a half-written db.json.
    fd, tmp = tempfile.mkstemp(dir=DB_PATH.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(db, f, indent=2)
        f.write("\n")
    os.replace(tmp, DB_PATH)


def _find(db: dict, user_id: int, session_id: int) -> dict:
    for session in db["sessions"]:
        if session["session_id"] == session_id and session["user_id"] == user_id:
            return session
    raise HTTPException(status_code=404, detail="Session not found")


def _new_session_id(db: dict) -> int:
    taken = {s["session_id"] for s in db["sessions"]}
    while (session_id := random.randint(100_000, 999_999)) in taken:
        pass
    return session_id


def play(user_id: int, data: SessionCreate) -> Session:
    """
    Create a play session for the user. This will create a new session and return it.
    """
    with _lock:
        db = _load()
        session = Session(
            session_id=_new_session_id(db),
            user_id=user_id,
            timestamp=int(time.time()),
            device_id=data.device_id,
            status="active",
            song_id=data.song_id,
        )
        db["sessions"].append(session.model_dump())
        _save(db)
    return session


def pause(user_id: int, session_id: int) -> Session:
    """
    Pause the session. This will update the session status to "paused".
    """
    with _lock:
        db = _load()
        session = _find(db, user_id, session_id)
        if session["status"] != "active":
            raise HTTPException(status_code=409, detail=f"Cannot pause a {session['status']} session")
        session["status"] = "paused"
        _save(db)
    return Session(**session)


def expire(user_id: int, session_id: int) -> Session:
    """
    Expire the session. This will update the session status to "expired".
    """
    with _lock:
        db = _load()
        session = _find(db, user_id, session_id)
        if session["status"] == "expired":
            raise HTTPException(status_code=409, detail="Session already expired")
        session["status"] = "expired"
        _save(db)
    return Session(**session)
