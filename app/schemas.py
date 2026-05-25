from pydantic import BaseModel
from typing import Optional


class PropertyFilter(BaseModel):
    area: str
    min_price: Optional[int]
    max_price: Optional[int]

    min_rooms: Optional[float]
    max_rooms: Optional[float]

    min_space: Optional[int]
    max_space: Optional[int]

    balcony: Optional[bool]
