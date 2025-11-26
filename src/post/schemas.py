from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Hashtag(BaseModel):
    id: int
    name: str

class PostCreate(BaseModel):
    content: str
    image: Optional[str] =None
    location: Optional[str] = None

class Post(PostCreate):
    id: int
    author_id: int
    likes_count: int
    created_at: datetime = Field(alias='created_dt')

    class Config:
        orm_mode = True
        allow_population_by_field_name = True