from fastapi_users.db import BeanieBaseUser, BeanieUserDatabase
from beanie import Document, init_beanie, PydanticObjectId
from beanie.operators import Or
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel
from pymongo.collation import Collation

from pydantic import Field
from asyncio import get_event_loop

from app.utils import get_timestamp

from typing import Optional


class BaseDocument(Document):
    created_at: int = Field(default_factory=get_timestamp)


class User(BeanieBaseUser, BaseDocument):
    class Settings(BeanieBaseUser.Settings):
        name: str = "users"
        username_collation = Collation("en", strength=2)

    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

User.Settings.indexes.extend([
    IndexModel("username", unique=True),
    IndexModel("username", name="case_insensitive_username_index", collation=User.Settings.username_collation)
])


class Post(BaseDocument):
    class Settings:
        name: str = "posts"

    title: str
    content: str
    preview_image_path: Optional[str] = None
    author_id: PydanticObjectId
    is_pinned: bool = False
    edited_at: Optional[int] = None


class PostReaction(BaseDocument):
    class Settings:
        name: str = "post_reactions"

    user_id: PydanticObjectId
    post_id: PydanticObjectId
    reaction: str


async def user_db_get_by_email_or_username(self, username: str) -> Optional[User]:
    return await self.user_model.find_one(
        Or(
            self.user_model.email == username,
            self.user_model.username == username
        ),
        collation=self.user_model.Settings.username_collation,
    )

BeanieUserDatabase.get_by_email_or_username = user_db_get_by_email_or_username

async def get_user_db() -> BeanieUserDatabase:
    yield BeanieUserDatabase(User)


async def init_db(db_uri: str, db_name: str) -> None:
    client: AsyncIOMotorClient = AsyncIOMotorClient(db_uri)
    client.get_io_loop = get_event_loop

    await init_beanie(
        database = client.get_database(db_name),
        document_models = [
            User,
            Post,
            PostReaction
        ]
    )
