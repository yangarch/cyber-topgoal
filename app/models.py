from pydantic import BaseModel
from typing import Optional

class Track(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    duration: float
    path: str
class Track(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    duration: float
    path: str
    has_cover: bool

class PublicTrack(BaseModel):
    id: str
    title: str
    artist: str
    album: str
    duration: float
    has_cover: bool

class CommentCreate(BaseModel):
    nickname: str
    content: str

class Comment(CommentCreate):
    id: int
    created_at: str
