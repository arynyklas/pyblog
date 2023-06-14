from fastapi import APIRouter, Depends, status, HTTPException

from pathlib import Path
from beanie import PydanticObjectId
from uuid import uuid4
from shutil import copyfileobj

from app.auth_backend import depends_current_active_user, UserManager, get_user_manager, get_user_db
from app.db import User, Post, PostReaction
from app import STARTUP_COROS, constants, errors, schemas
from app.config import config

from typing import Union, Optional, Dict, Tuple, List


router: APIRouter = APIRouter()

STATIC_POSTS_DIRPATH: Path = constants.parent_dirpath / "static" / "posts"

if not STATIC_POSTS_DIRPATH.is_dir():
    STATIC_POSTS_DIRPATH.mkdir()

user_manager: UserManager


async def parse_post_read_model(post: Post, known_authors: Optional[Dict[PydanticObjectId, str]]=None) -> Union[Tuple[Union[schemas.PostRead, None], Dict[PydanticObjectId, str]], Union[schemas.PostRead, None]]:
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

    post_read: schemas.PostRead = schemas.PostRead(
        id = post.id,
        title = post.title,
        content = post.content,
        preview_image_url = (
            f"/static/posts/{post.preview_image_path}"
            if post.preview_image_path
            else
            None
        ),
        author = schemas.PostAuthorRead(
            id = author_id,
            username = author_username
        ),
        edited_at = post.edited_at,
        created_at = post.created_at,
        reactions = {
            reaction: await PostReaction.find(
                PostReaction.post_id == post.id,
                PostReaction.reaction == reaction
            ).count()
            for reaction in config.reactions_list
        }
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
    response_model = schemas.PostRead,
    summary = "Show one post"
)
async def get_single_post_route(
    post_id: schemas.Id
) -> schemas.PostRead:
    post: Union[Post, None] = await Post.get(post_id)

    if not post:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = errors.ErrorStrings.POST_NOT_FOUND
        )

    return await parse_post_read_model(
        post = post
    )


@router.get(
    path = "/list",
    response_model = schemas.PostReadList,
    summary = "Show list of posts"
)
async def get_list_posts_route(
    offset: int = 0,
    limit: int = 0
) -> schemas.PostReadList:
    if limit == 0:
        limit = config.api_posts_limit

    post_read_list: List[schemas.PostRead] = []
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

    return schemas.PostReadList(
        posts = post_read_list
    )


@router.post(
    path = "/single",
    response_model = schemas.PostRead,
    summary = "Create new post",
    responses = {
        **errors.ErrorResponses.USER_AUTH,
        **errors.ErrorResponses.INVALID_CONTENT_TYPE
    }
)
async def create_post_route(
    user: User = depends_current_active_user,
    post_create: schemas.PostCreate = Depends()
) -> schemas.PostRead:
    preview_image_path: Union[str, None] = None

    if post_create.preview_image:
        extension: str = post_create.preview_image.filename.split(".")[-1]

        if extension not in constants.image_extensions:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = errors.ErrorStrings.INVALID_CONTENT_TYPE
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


@router.patch(
    path = "/single",
    response_model = schemas.PostRead,
    summary = "Update post",
    responses = {
        **errors.ErrorResponses.USER_AUTH,
        **errors.ErrorResponses.INVALID_CONTENT_TYPE
    }
)
async def update_post_route(
    user: User = depends_current_active_user,
    post_update: schemas.PostUpdate = Depends()
) -> schemas.PostRead:
    post: Union[Post, None] = await Post.get(post_update.post_id)

    if not post:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = errors.ErrorStrings.POST_NOT_FOUND
        )

    preview_image_path: Union[str, None] = None

    if post_update.preview_image:
        extension: str = post_update.preview_image.filename.split(".")[-1]

        if extension not in constants.image_extensions:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = errors.ErrorStrings.INVALID_CONTENT_TYPE
            )

        if post_update.delete_old_preview_image:
            if post.preview_image_path:
                (STATIC_POSTS_DIRPATH / post.preview_image_path).unlink()
            else:
                raise HTTPException(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    detail = "INVALID_ARGUMENT - preview_image_path" # TODO
                )

        preview_image_path: str = f"{uuid4()}.{extension}"

        with (STATIC_POSTS_DIRPATH / preview_image_path).open("wb") as file:
            copyfileobj(post_update.preview_image.file, file)

    post: Post = Post(
        title = post_update.title,
        content = post_update.content,
        preview_image_path = preview_image_path,
        author_id = user.id
    )

    await post.insert()

    return await parse_post_read_model(
        post = post
    )


@router.post(
    path = "/reaction",
    response_model = schemas.PostReactionRead,
    summary = "Set reaction",
    responses = {
        **errors.ErrorResponses.USER_AUTH,
        **errors.ErrorResponses.POST_NOT_FOUND,
        **errors.ErrorResponses.INVALID_REACTION,
        **errors.ErrorResponses.REACTION_NOT_FOUND
    }
)
async def new_post_route(
    user: User = depends_current_active_user,
    post_reaction_create: schemas.PostReactionCreate = Depends()
) -> schemas.PostReactionRead:
    post: Union[Post, None] = await Post.get(post_reaction_create.post_id)

    if not post:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = errors.ErrorStrings.POST_NOT_FOUND
        )

    reaction: Union[str, None] = post_reaction_create.reaction

    if reaction and reaction not in config.reactions_list:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = errors.ErrorStrings.INVALID_REACTION
        )

    post_reaction: Union[PostReaction, None] = await PostReaction.find_one(
        PostReaction.user_id == user.id,
        PostReaction.post_id == post.id
    )

    is_added: bool = False
    is_changed: bool = False
    is_removed: bool = False

    if not reaction:
        if not post_reaction:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = errors.ErrorStrings.REACTION_NOT_FOUND
            )

        await post_reaction.delete()

        is_removed = True

    else:
        is_added = not bool(post_reaction)

        if post_reaction:
            if post_reaction.reaction != reaction:
                post_reaction.reaction = reaction

                await post_reaction.save()

                is_changed = True

        else:
            await PostReaction(
                user_id = user.id,
                post_id = post.id,
                reaction = reaction
            ).insert()

    return schemas.PostReactionRead(
        reaction = post_reaction_create.reaction,
        is_added = is_added,
        is_changed = is_changed,
        is_removed = is_removed
    )
