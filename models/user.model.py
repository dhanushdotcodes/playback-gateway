from pydantic import BaseModel, Field
from typing import Literal

class User(BaseModel):
  id: int
  name: str
  email: str
  subscriptionPlan: Literal["plus", "premium"]