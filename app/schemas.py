from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status, UploadFile
from fastapi_users import schemas
from fastapi_users_db_beanie import ObjectIDIDMixin
from pydantic import BaseModel

from app import errors

from typing import Dict, Optional, List, Union


class Id(PydanticObjectId):
    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            v = v.decode("utf-8")
        try:
            return PydanticObjectId(v)

        except InvalidId:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = errors.ErrorStrings.POST_NOT_FOUND
            )


class UserRead(schemas.BaseUser[ObjectIDIDMixin]):
    username: str

class UserCreate(schemas.BaseUserCreate):
    username: str

class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str]


class PostAuthorRead(BaseModel):
    id: Id
    username: Optional[str] = None

class PostRead(BaseModel):
    id: Id
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

class PostUpdate(BaseModel):
    post_id: Id
    title: str
    content: str
    preview_image: Optional[UploadFile] = None
    delete_old_preview_image: bool = True

class PostReactionRead(BaseModel):
    reaction: Union[str, None]
    is_added: bool
    is_changed: bool
    is_removed: bool

class PostReactionCreate(BaseModel):
    post_id: Id
    reaction: Union[str, None] = None
