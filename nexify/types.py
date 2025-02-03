from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from nexify.responses import HttpResponse

EventType = dict[str, Any]
ContextType = dict[str, Any]

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
Handler = Callable[[dict, dict], Any]
IncEx = set[int] | set[str] | dict[int, Any] | dict[str, Any]

ExceptionHandler = Callable[[EventType, ContextType, Any], "HttpResponse"]
