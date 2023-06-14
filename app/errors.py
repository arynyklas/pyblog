from pydantic import BaseModel
from enum import Enum
from fastapi import status

from typing import Tuple


class ErrorModel(BaseModel):
    detail: str


def _build_error_response(error: Tuple[int, str]) -> dict:
    return {
        error[0]: {
            "model": ErrorModel,
            "description": error[1],
            "content": {
                "application/json": {
                    "example": {
                        "detail": error[1]
                    }
                }
            }
        }
    }


class ErrorStrings(str, Enum):
    USER_AUTH = "Missing token or inactive user."
    INVALID_CONTENT_TYPE = "INVALID_CONTENT_TYPE"
    POST_NOT_FOUND = "POST_NOT_FOUND"
    INVALID_REACTION = "INVALID_REACTION"
    REACTION_NOT_FOUND = "REACTION_NOT_FOUND"


class _Errors(Tuple[int, str], Enum):
    USER_AUTH = (
        status.HTTP_401_UNAUTHORIZED,
        ErrorStrings.USER_AUTH
    )

    INVALID_CONTENT_TYPE = (
        status.HTTP_400_BAD_REQUEST,
        ErrorStrings.INVALID_CONTENT_TYPE
    )

    POST_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        ErrorStrings.POST_NOT_FOUND
    )

    INVALID_REACTION = (
        status.HTTP_400_BAD_REQUEST,
        ErrorStrings.INVALID_REACTION
    )

    REACTION_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        ErrorStrings.REACTION_NOT_FOUND
    )


class ErrorResponses(dict, Enum):
    USER_AUTH = _build_error_response(_Errors.USER_AUTH)
    INVALID_CONTENT_TYPE = _build_error_response(_Errors.INVALID_CONTENT_TYPE)
    POST_NOT_FOUND = _build_error_response(_Errors.POST_NOT_FOUND)
    INVALID_REACTION = _build_error_response(_Errors.INVALID_REACTION)
    REACTION_NOT_FOUND = _build_error_response(_Errors.REACTION_NOT_FOUND)
