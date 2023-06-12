from fastapi import Request, Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users_db_beanie import ObjectIDIDMixin

from fastapi_users import models as fu_models, exceptions as fu_exceptions

from app.db import User, get_user_db
from app.config import config

from typing import Optional


cookie_transport: CookieTransport = CookieTransport(
    # cookie_name = "userauth",
    cookie_max_age = config.secrets_lifetime
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret = config.secret,
        lifetime_seconds = config.secrets_lifetime,
        algorithm = "HS256"
    )


auth_backend: AuthenticationBackend = AuthenticationBackend(
    name = "jwt",
    transport = cookie_transport,
    get_strategy = get_jwt_strategy
)


class UserManager(ObjectIDIDMixin, BaseUserManager[User, ObjectIDIDMixin]):
    reset_password_token_secret: str = config.secret
    reset_password_token_lifetime_seconds: int = config.verifications_lifetime
    verification_token_secret: str = config.secret
    verification_token_lifetime_seconds: int = config.verifications_lifetime

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None
    ) -> None:
        print(f"User {user.id} ({user.email}) has registered.")

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None
    ) -> None:
        print(f"User {user.id} ({user.email}) has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None
    ) -> None:
        print(f"Verification requested for user {user.id} ({user.email}). Verification token: {token}")

    # async def validate_password(
    #     self,
    #     password: str,
    #     user: Union[UserCreate, User],
    # ) -> None:
    #     if len(password) < 8:
    #         raise InvalidPasswordException(
    #             reason="Password should be at least 8 characters"
    #         )
    #     if user.email in password:
    #         raise InvalidPasswordException(
    #             reason="Password should not contain e-mail"
    #         )


async def user_manager_get_by_email_or_username(self, username: str) -> fu_models.UP:
    user: fu_models.UP = await self.user_db.get_by_email_or_username(username)

    if user is None:
        raise fu_exceptions.UserNotExists()

    return user

async def user_manager_authenticate(
    self: UserManager,
    credentials: OAuth2PasswordRequestForm
) -> Optional[fu_models.UP]:
    try:
        user = await self.get_by_email_or_username(credentials.username)

    except fu_exceptions.UserNotExists:
        self.password_helper.hash(credentials.password)
        return None

    verified, updated_password_hash = self.password_helper.verify_and_update(
        credentials.password,
        user.hashed_password
    )

    if not verified:
        return None

    if updated_password_hash is not None:
        await self.user_db.update(
            user,
            {
                "hashed_password": updated_password_hash
            }
        )

    return user

UserManager.get_by_email_or_username = user_manager_get_by_email_or_username
UserManager.authenticate = user_manager_authenticate

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(
        user_db = user_db
    )


fastapi_users: FastAPIUsers[User, ObjectIDIDMixin] = FastAPIUsers[User, ObjectIDIDMixin](
    get_user_manager = get_user_manager,
    auth_backends = [
        auth_backend
    ]
)


current_active_user = fastapi_users.current_user(
    active = True
)

depends_current_active_user = Depends(current_active_user)
