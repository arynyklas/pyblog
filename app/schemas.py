from fastapi_users import schemas
from fastapi_users_db_beanie import ObjectIDIDMixin
from pydantic import BaseModel
from beanie import PydanticObjectId
from fastapi import UploadFile

from typing import Optional, Dict, List


class UserRead(schemas.BaseUser[ObjectIDIDMixin]):
    username: str

class UserCreate(schemas.BaseUserCreate):
    username: str

class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str]


class PostAuthorRead(BaseModel):
    id: PydanticObjectId
    username: Optional[str] = None

class PostRead(BaseModel):
    id: PydanticObjectId
    title: str
    content: str
    preview_image_url: Optional[str] = None
    author: PostAuthorRead
    is_pinned: bool = False
    edited_at: Optional[int] = None
    created_at: int
    reactions: Dict[str, int]

class PostReadList(BaseModel):
    posts: List[PostRead]

class PostCreate(BaseModel):
    title: str
    content: str
    preview_image: Optional[UploadFile] = None
