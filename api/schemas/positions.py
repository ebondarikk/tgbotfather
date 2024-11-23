from typing import List, Optional

from pydantic import BaseModel


class PositionPayload(BaseModel):
    password: str
    data: List[dict]
    bot_id: int
    user_id: int
    message_id: int


class PositionsFreeze(BaseModel):
    position_key: str
    subitems: Optional[List[str]] = None


class PositionFreezePayload(BaseModel):
    bot_id: int | str
    user_id: int | str
    data: List[PositionsFreeze]
