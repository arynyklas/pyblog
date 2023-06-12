from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app import constants
from app.config import config

import fastapi.openapi.utils as fastapi_openapi_utils

from typing import List, Awaitable


def generate_operation_summary(*, route: APIRouter, method: str) -> str:
    if route.summary:
        return route.summary

    return ""

fastapi_openapi_utils.generate_operation_summary = generate_operation_summary


main_app: FastAPI = FastAPI(
    debug = True,
    docs_url = None,
    redoc_url = None
)


STARTUP_COROS: List[Awaitable] = [
    init_db(
        db_uri = config.db.uri,
        db_name = config.db.name
    )
]


@main_app.on_event("startup")
async def main_app_on_startup() -> None:
    for coro in STARTUP_COROS:
        await coro


def setup_app() -> None:
    from app import main, api

    main.mount(
        app = main_app
    )

    main_app.mount(
        path = "/api",
        app = api.api_app
    )

    main_app.mount(
        path = "/static",
        app = StaticFiles(
            directory = constants.parent_dirpath / "static"
        )
    )
