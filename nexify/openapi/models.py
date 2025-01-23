from typing import (
    Any,
    TypedDict,
)


class Example(TypedDict, total=False):
    summary: str | None
    description: str | None
    value: Any | None
    externalValue: str | None

    __pydantic_config__ = {"extra": "allow"}  # type: ignore
