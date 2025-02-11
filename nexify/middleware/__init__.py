import inspect
import logging
from abc import abstractmethod
from collections.abc import Callable
from contextlib import ExitStack, contextmanager
from typing import TYPE_CHECKING, Any

from nexify.dependencies.models import Dependant
from nexify.exceptions import RequestValidationError, ResponseValidationError
from nexify.responses import HttpResponse

if TYPE_CHECKING:  # pragma: no cover
    from nexify.operation import Operation
from nexify.types import ContextType, EventType, ExceptionHandler


class Middleware:
    @abstractmethod
    def __call__(self, route: "Operation", event: EventType, context: ContextType, call_next): ...


class ServerErrorMiddleware(Middleware):
    def __call__(self, route, event, context, call_next):
        try:
            return call_next(event, context)
        except Exception as e:
            logging.exception(e)  # TODO: Add more detailed logging
            return HttpResponse(status_code=500, content={"detail": "Internal Server Error"})


class ExceptionMiddleware(Middleware):
    def __init__(
        self,
        exception_handlers: dict[type[Exception], ExceptionHandler],
    ):
        self.exception_handlers = exception_handlers

    def __call__(self, route, event, context, call_next):
        try:
            return call_next(event, context)
        except Exception as e:
            for exception_type, handler in self.exception_handlers.items():
                if isinstance(e, exception_type):
                    return handler(event, context, e)
            raise e


class RenderMiddleware(Middleware):
    def __call__(self, route, event, context, call_next):
        content = call_next(event, context)

        if isinstance(content, HttpResponse):
            response = content
        else:
            response = route.response_class(content=content, status_code=route.status_code)

        return response.render()


class ResponseValidationMiddleware(Middleware):
    def __call__(self, route, event, context, call_next):
        content = call_next(event, context)
        if route.response_field is None:
            return content

        content, _errors = route.response_field.validate(content, loc=("response",))

        if _errors:
            raise ResponseValidationError(errors=_errors, body=content)

        return content


def is_gen_callable(call: Callable[..., Any]) -> bool:
    if inspect.isgeneratorfunction(call):
        return True
    dunder_call = getattr(call, "__call__", None)  # noqa: B004
    return inspect.isgeneratorfunction(dunder_call)


def solve_generator(*, call: Callable[..., Any], exit_stack: ExitStack, sub_values: dict[str, Any]) -> Any:
    if is_gen_callable(call):
        cm = contextmanager(call)(**sub_values)
    return exit_stack.enter_context(cm)


def solve_sub_dependency(dependant: Dependant, event, context, exit_stack: ExitStack) -> Any:
    parsed_data = {}
    errors = []
    for field in (
        dependant.path_params
        + dependant.query_params
        + dependant.header_params
        + dependant.cookie_params
        + dependant.body_params
        + dependant.event_params
        + dependant.context_params
    ):
        source = field.field_info.get_source(event, context)
        value, errors_ = field.field_info.get_value_from_source(source)
        if errors_:
            errors.extend(errors_)
            continue

        v_, errors_ = field.validate(
            value,
            loc=(field.field_info.__class__.__name__.lower(), field.name),
        )
        if errors_:
            errors.extend(errors_)
            continue

        parsed_data[field.name] = v_

    if errors:
        raise RequestValidationError(errors, body=event)

    for depends in dependant.dependencies:
        parsed_data[depends.name] = solve_sub_dependency(depends, event, context, exit_stack=exit_stack)

    if is_gen_callable(dependant.call):
        return solve_generator(call=dependant.call, exit_stack=exit_stack, sub_values=parsed_data)

    return dependant.call(**parsed_data)


def solve_dependencies(dependant: Dependant, event, context, exit_stack: ExitStack) -> dict[str, Any]:
    parsed_data = {}
    errors = []
    for field in (
        dependant.path_params
        + dependant.query_params
        + dependant.header_params
        + dependant.cookie_params
        + dependant.body_params
        + dependant.event_params
        + dependant.context_params
    ):
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

    for depends in dependant.dependencies:
        result = solve_sub_dependency(depends, event, context, exit_stack=exit_stack)
        if depends.name is not None:
            parsed_data[depends.name] = result

    return parsed_data


class RequestParsingMiddleware(Middleware):
    def __call__(self, route, event, context, call_next):
        with ExitStack() as exit_stack:
            parsed_data = solve_dependencies(route.dependant, event, context, exit_stack=exit_stack)
            return call_next(event, context, _nexify_parsed_data=parsed_data)
