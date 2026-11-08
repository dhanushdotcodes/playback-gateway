from pydantic import BaseModel
from typing import Literal

class Session(BaseModel):
    session_id: str
    user_id: int
    timestamp: int
    deviceId: str
    status: Literal["active", "expired"]
    song_id: str
    created_at: str
    expires_at: str