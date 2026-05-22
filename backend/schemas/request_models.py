from pydantic import BaseModel, Field
from typing import Optional

class RecommendRequest(BaseModel):
    time_available: int = Field(gt=0, description="Available playtime in minutes, must be greater than 0")
    vibe: str | list[str] 
    platform: Optional[str] = None
    modifier: Optional[str] = None
    max_difficulty: Optional[int] = None
    exclude_titles: Optional[list[str]] = []