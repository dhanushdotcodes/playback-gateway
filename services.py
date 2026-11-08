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

HEARTBEAT_TIMEOUT = 15  # seconds without a heartbeat before a session is expired

# Max sessions a user can have playing at the same time, per subscription plan.
PLAN_DEVICE_LIMIT = {"free": 1, "plus": 1, "premium": 2}

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
        now = int(time.time())

        # Sessions whose client stopped heart-beating (or never connected) no longer hold a slot.
        for s in db["sessions"]:
            if s["status"] != "expired" and now - s.get("last_heartbeat", 0) > HEARTBEAT_TIMEOUT:
                s["status"] = "expired"

        user = next((u for u in db["users"] if u["id"] == user_id), None)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        active = [s for s in db["sessions"] if s["user_id"] == user_id and s["status"] == "active"]
        # A device plays one thing at a time: starting a new song replaces its previous session.
        for s in active:
            if s["device_id"] == data.device_id:
                s["status"] = "expired"
        active = [s for s in active if s["status"] == "active"]
        if len(active) >= PLAN_DEVICE_LIMIT[user["subscription_plan"]]:
            detail = "Device limit reached" if user["subscription_plan"] == "premium" else "Upgrade your plan"
            raise HTTPException(status_code=409, detail=detail)

        session = Session(
            session_id=_new_session_id(db),
            user_id=user_id,
            timestamp=now,
            device_id=data.device_id,
            status="active",
            song_id=data.song_id,
            last_heartbeat=now,
        )
        db["sessions"].append(session.model_dump())
        _save(db)
    return session


def heartbeat(user_id: int, session_id: int) -> Session:
    """
    Record a heartbeat for the session and return it (so the caller can see if it was expired).
    """
    with _lock:
        db = _load()
        session = _find(db, user_id, session_id)
        if session["status"] != "expired":
            session["last_heartbeat"] = int(time.time())
            _save(db)
    return Session(**session)


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
