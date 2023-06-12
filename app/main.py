from fastapi import APIRouter, Request, FastAPI
from fastapi.responses import HTMLResponse

from app import constants


router: APIRouter = APIRouter()


@router.api_route(
    path = "/",
    response_class = HTMLResponse
)
async def main_app_index_route(request: Request) -> HTMLResponse:
    return constants.templates.TemplateResponse(
        name = "index.html",
        context = {
            "request": request
        }
    )


def mount(app: FastAPI) -> None:
    app.routes.extend(router.routes)
