from pydantic import BaseModel


class ErrorModel(BaseModel):
    detail: str

INVALID_CONTENT_TYPE_STR: str = "INVALID_CONTENT_TYPE"

INVALID_CONTENT_TYPE: dict = ErrorModel(
    detail = INVALID_CONTENT_TYPE_STR
).dict()
