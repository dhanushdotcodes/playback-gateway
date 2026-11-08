from pydantic import BaseModel, Field, EmailStr
from typing import Literal

class User(BaseModel):
  id: int
  name: str
  email: EmailStr
  subscription_plan: Literal["free", "plus", "premium"]
