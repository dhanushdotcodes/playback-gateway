from pydantic import BaseModel
from typing import Literal

class Session(BaseModel):
    session_id: int
    user_id: int
    timestamp: int
    device_id: str
    status: Literal["active", "paused", "expired"]
    song_id: int

class SessionCreate(BaseModel):
    device_id: str
    song_id: int

class SessionRef(BaseModel):
    session_id: int
