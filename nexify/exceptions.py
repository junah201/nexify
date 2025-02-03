from collections.abc import Mapping, Sequence
from typing import Any


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str | None = None, headers: Mapping[str, str] | None = None) -> None:
        self.detail = detail or f"{status_code} error"
        self.status_code = status_code
        self.detail = detail
        self.headers = headers

    def __str__(self) -> str:
        return f"{self.status_code}: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"


class ValidationException(Exception):
    def __init__(self, errors: Sequence[Any]) -> None:
        self._errors = errors

    @property
    def errors(self) -> Sequence[Any]:
        return self._errors


class RequestValidationError(ValidationException):
    def __init__(self, errors: Sequence[Any], *, body: Any = None) -> None:
        super().__init__(errors)
        self.body = body


class ResponseValidationError(ValidationException):
    def __init__(self, errors: Sequence[Any], *, body: Any = None) -> None:
        super().__init__(errors)
        self.body = body

    def __str__(self) -> str:
        message = f"{len(self._errors)} validation errors:\n"
        for err in self._errors:
            message += f"  {err}\n"
        return message
