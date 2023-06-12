from fastapi import APIRouter, Depends, status, HTTPException

from pathlib import Path
from beanie import PydanticObjectId
from uuid import uuid4
from shutil import copyfileobj

from app.auth_backend import depends_current_active_user, UserManager, get_user_manager, get_user_db
from app.db import User, Post, POST_DEFAULT_REACTIONS
from app import STARTUP_COROS
from app.schemas import PostAuthorRead, PostRead, PostReadList, PostCreate
from app import constants, common
from app.config import config

from typing import Union, Optional, Dict, Tuple, List


router: APIRouter = APIRouter()

STATIC_POSTS_DIRPATH: Path = constants.parent_dirpath / "static" / "posts"

if not STATIC_POSTS_DIRPATH.is_dir():
    STATIC_POSTS_DIRPATH.mkdir()

user_manager: UserManager


async def parse_post_read_model(post: Union[Post, None], known_authors: Optional[Dict[PydanticObjectId, str]]=None) -> Union[Tuple[Union[PostRead, None], Dict[PydanticObjectId, str]], Union[PostRead, None]]:
    if not post:
        return

    author_id: PydanticObjectId = post.author_id
    author_username: str

    if known_authors and author_id in known_authors:
        author_username = known_authors[author_id]

    else:
        author_username = (
            await user_manager.get(author_id)
        ).username

        if known_authors:
            known_authors[author_id] = author_username

    post_read: PostRead = PostRead(
        id = post.id,
        title = post.title,
        content = post.content,
        preview_image_url = (
            f"/static/posts/{post.preview_image_path}"
            if post.preview_image_path
            else
            None
        ),
        author = PostAuthorRead(
            id = author_id,
            username = author_username
        ),
        reactions = POST_DEFAULT_REACTIONS,
        edited_at = post.edited_at,
        created_at = post.created_at
    )

    if isinstance(known_authors, dict):
        return post_read, known_authors

    return post_read


async def on_startup() -> None:
    global user_manager

    user_manager = [
        user_manager
        async for user_manager in get_user_manager(
            user_db = [
                user_db
                async for user_db in get_user_db()
            ][0]
        )
    ][0]

STARTUP_COROS.append(on_startup())


@router.get(
    path = "/single",
    response_model = PostRead,
    summary = "Show one post"
)
async def get_single_post_route(
    post_id: PydanticObjectId
) -> PostRead:
    return await parse_post_read_model(
        post = await Post.get(post_id)
    )


@router.get(
    path = "/list",
    response_model = PostReadList,
    summary = "Show list of posts"
)
async def get_list_posts_route(
    offset: int = 0,
    limit: int = 0
) -> PostReadList:
    if limit == 0:
        limit = config.api_posts_limit

    post_read_list: List[PostRead] = []
    known_authors: Dict[PydanticObjectId, str] = {}

    for post in await Post.find_all().skip(
        n = offset
    ).limit(
        n = min(limit, config.api_posts_limit)
    ).to_list():
        post_read, known_authors = await parse_post_read_model(
            post = post,
            known_authors = known_authors
        )

        post_read_list.append(post_read)

    return PostReadList(
        posts = post_read_list
    )


@router.post(
    path = "/single",
    response_model = PostRead,
    summary = "Create new post",
    responses = {
        status.HTTP_400_BAD_REQUEST: {
            "model": common.ErrorModel,
            "description": "Invalid Content Type Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": common.INVALID_CONTENT_TYPE_STR
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user."
        }
    }
)
async def new_post_route(
    user: User = depends_current_active_user,
    post_create: PostCreate = Depends()
) -> PostRead:
    preview_image_path: Union[str, None] = None

    if post_create.preview_image:
        extension: str = post_create.preview_image.filename.split(".")[-1]

        if extension not in constants.image_extensions:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = common.INVALID_CONTENT_TYPE
            )

        preview_image_path: str = f"{uuid4()}.{extension}"

        with (STATIC_POSTS_DIRPATH / preview_image_path).open("wb") as file:
            copyfileobj(post_create.preview_image.file, file)

    post: Post = Post(
        title = post_create.title,
        content = post_create.content,
        preview_image_path = preview_image_path,
        author_id = user.id
    )

    await post.insert()

    return await parse_post_read_model(
        post = post
    )
