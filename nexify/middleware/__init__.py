from abc import abstractmethod
from typing import TYPE_CHECKING

from nexify.exceptions import RequestValidationError, ResponseValidationError
from nexify.responses import HttpResponse

if TYPE_CHECKING:  # pragma: no cover
    from nexify.routing import Route
from nexify.types import ContextType, EventType, ExceptionHandler


class Middleware:
    @abstractmethod
    def __call__(self, route: "Route", event: EventType, context: ContextType, call_next, **kwargs): ...


class ExceptionMiddleware(Middleware):
    def __init__(
        self,
        exception_handlers: dict[type[Exception], ExceptionHandler],
    ):
        self.exception_handlers = exception_handlers

    def __call__(self, route, event, context, call_next, **kwargs):
        try:
            return call_next(event, context, **kwargs)
        except Exception as e:
            for exception_type, handler in self.exception_handlers.items():
                if isinstance(e, exception_type):
                    return handler(event, context, e)
            raise e


class RenderMiddleware(Middleware):
    def __call__(self, route, event, context, call_next, **kwargs):
        content = call_next(event, context, **kwargs)

        if isinstance(content, HttpResponse):
            response = content
        else:
            response = route.response_class(content=content, status_code=route.status_code)

        return response.render()


class ResponseValidationMiddleware(Middleware):
    def __call__(self, route, event, context, call_next, **kwargs):
        content = call_next(event, context, **kwargs)
        if route.response_field is None:
            return content

        content, _errors = route.response_field.validate(content, loc=("response",))

        if _errors:
            raise ResponseValidationError(errors=_errors, body=content)

        return content


class RequestParsingMiddleware(Middleware):
    def __call__(self, route, event, context, call_next, **kwargs):
        parsed_data = {}
        errors = []
        for field in route.fields:
            source = field.field_info.get_source(event, context)
            value, errors_ = field.field_info.get_value_from_source(source)
            if errors_:
                errors.extend(errors_)
                continue

            v_, errors_ = field.validate(
                value,
                loc=(
                    field.field_info.__class__.__name__.lower(),
                    field.name,
                ),
            )
            if errors_:
                errors.extend(errors_)
                continue

            parsed_data[field.name] = v_

        if errors:
            raise RequestValidationError(errors, body=event)

        return call_next(event, context, _parsed_data=parsed_data, **kwargs)
