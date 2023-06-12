from fastapi import APIRouter

from app.auth_backend import fastapi_users, auth_backend
from app.schemas import UserRead, UserCreate


current_active_user = fastapi_users.current_user(
    active = True
)


router: APIRouter = APIRouter()


router.routes.extend(
    fastapi_users.get_auth_router(
        backend = auth_backend
    ).routes
)

router.routes.extend(
    fastapi_users.get_register_router(
        user_schema = UserRead,
        user_create_schema = UserCreate
    ).routes
)

router.routes.extend(
    fastapi_users.get_verify_router(UserRead).routes
)

router.routes.extend(
    fastapi_users.get_reset_password_router().routes
)
