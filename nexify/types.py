from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:  # pragma: no covers
    from nexify.responses import HttpResponse
    from nexify.routing import Route

EventType = dict[str, Any]
ContextType = dict[str, Any]

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
HandlerType = Callable[[dict, dict], Any]
IncEx = set[int] | set[str] | dict[int, Any] | dict[str, Any]

ExceptionHandler = Callable[[EventType, ContextType, Any], "HttpResponse"]
# MiddlewareType = Callable[["Route", EventType, ContextType, Callable, Any], Any]
MiddlewareType = TypeVar("MiddlewareType", bound=Callable[["Route", EventType, ContextType, Callable, Any], Any])
