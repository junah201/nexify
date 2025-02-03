from nexify.encoders import jsonable_encoder
from nexify.exceptions import HTTPException, RequestValidationError, ResponseValidationError
from nexify.responses import JSONResponse, Response
from nexify.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
from nexify.types import ContextType, EventType


def http_exception_handler(event: EventType, _context: ContextType, exc: HTTPException) -> Response:
    headers = getattr(exc, "headers", None)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=headers)


def request_validation_exception_handler(
    event: EventType, _context: ContextType, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors)},
    )


def response_validation_exception_handler(
    event: EventType, _context: ContextType, exc: ResponseValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
