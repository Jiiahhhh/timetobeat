from pydantic import BaseModel
from typing import Optional

class RecommendRequest(BaseModel):
    time_available: int
    vibe: str | list[str] 
    platform: Optional[str] = None
    modifier: Optional[str] = None
    max_difficulty: Optional[int] = None
    exclude_titles: Optional[list[str]] = []