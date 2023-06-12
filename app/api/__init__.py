from fastapi import FastAPI

from app.api import auth, posts
from app.auth_backend import fastapi_users
from app.schemas import UserRead, UserUpdate
from app.config import config


api_app: FastAPI = FastAPI(
    title = "Aryn PyBlog",
    description = "PyBlog vs hausmik",
    version = config.version,
    swagger_ui_oauth2_redirect_url = None
)


api_app.routes.append(
    fastapi_users.get_users_router(
        user_schema = UserRead,
        user_update_schema = UserUpdate
    ).routes[0]
)


api_app.include_router(
    router = auth.router,
    prefix = "/auth",
    tags = [
        "auth"
    ]
)


api_app.include_router(
    router = posts.router,
    prefix = "/posts",
    tags = [
        "posts"
    ]
)
