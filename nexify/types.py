from collections.abc import Callable
from typing import Any, TypeVar

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
Handler = Callable[[dict, dict], Any]
