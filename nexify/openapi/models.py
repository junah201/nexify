from typing import (
    Any,
    TypedDict,
)

from pydantic_core import PydanticUndefined

Undefined: Any = PydanticUndefined


class Example(TypedDict, total=False):
    """
    OpenAPI Example
    """

    summary: str | None
    description: str | None
    value: Any | None
    externalValue: str | None

    __pydantic_config__ = {"extra": "allow"}  # type: ignore
