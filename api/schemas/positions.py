from typing import List

from pydantic import BaseModel


class PositionPayload(BaseModel):
    password: str
    data: List[dict]
    bot_id: int
    user_id: int
    message_id: int
