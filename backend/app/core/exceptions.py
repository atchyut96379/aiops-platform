from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception with HTTP mapping."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "app_error",
        details: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_404_NOT_FOUND,
            code=kwargs.pop("code", "not_found"),
            **kwargs,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_409_CONFLICT,
            code=kwargs.pop("code", "conflict"),
            **kwargs,
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", **kwargs: Any) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=kwargs.pop("code", "unauthorized"),
            **kwargs,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden", **kwargs: Any) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_403_FORBIDDEN,
            code=kwargs.pop("code", "forbidden"),
            **kwargs,
        )


class ValidationAppError(AppException):
    def __init__(self, message: str = "Validation error", **kwargs: Any) -> None:
        super().__init__(
            message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=kwargs.pop("code", "validation_error"),
            **kwargs,
        )


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", str(detail))
        code = detail.get("code", "http_error")
        details = detail.get("details")
    else:
        message = str(detail)
        code = "http_error"
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message, "details": details}},
        headers=getattr(exc, "headers", None),
    )
