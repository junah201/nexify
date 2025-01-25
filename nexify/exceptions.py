from collections.abc import Sequence
from typing import Any


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
