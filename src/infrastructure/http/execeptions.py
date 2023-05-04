import logging
import traceback

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from apps.shared.domain import ErrorResponse, ErrorResponseMulti
from apps.shared.exception import BaseError

logger = logging.getLogger("mindlogger_backend")


def custom_base_errors_handler(_: Request, error: BaseError) -> JSONResponse:
    """This function is called if the BaseError was raised."""
    response = ErrorResponseMulti(
        result=[
            ErrorResponse(
                message=error.error,
                type=error.type,
                path=getattr(error, "path", []),
            )
        ]
    )

    logger.error(response)

    return JSONResponse(
        response.dict(by_alias=True),
        status_code=error.status_code,
    )


def python_base_error_handler(_: Request, error: Exception) -> JSONResponse:
    """This function is called if the Exception was raised."""

    error_message = "".join(traceback.format_tb(error.__traceback__))
    response = ErrorResponseMulti(
        result=[ErrorResponse(message=f"Unhandled error: {error_message}")]
    )

    logger.error(response)

    return JSONResponse(
        content=jsonable_encoder(response.dict(by_alias=True)),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def pydantic_validation_errors_handler(
    _: Request, error: RequestValidationError
) -> JSONResponse:
    """This function is called if the Pydantic validation error was raised."""

    response = ErrorResponseMulti(
        result=[
            ErrorResponse(
                message=err["msg"],
                path=list(err["loc"]),
            )
            for err in error.errors()
        ]
    )

    logger.error(response)

    return JSONResponse(
        content=jsonable_encoder(response.dict(by_alias=True)),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )