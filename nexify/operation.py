from collections.abc import Callable
from typing import Annotated, Generic, TypeVar

from nexify.middleware import Middleware
from typing_extensions import Doc


class Operation:
    def __init__(self, handler: Callable, middlewares: list[Middleware] | None = None):
        self.handler = handler
        self.middlewares = middlewares or []

    def __call__(self, event, context):
        def call_next(event, context, index=0, **kwargs):
            if index < len(self.middlewares):
                return self.middlewares[index](
                    route=self,
                    event=event,
                    context=context,
                    call_next=lambda e, c, **new_kwargs: call_next(e, c, index + 1, **kwargs, **new_kwargs),
                )
            _parsed_data = kwargs.pop("_nexify_parsed_data", {})
            return self.handler(**_parsed_data)

        return call_next(event, context)


OperationT = TypeVar("OperationT", bound=Operation)


class OperationManager(Generic[OperationT]):
    def __init__(
        self,
        middlewares: Annotated[
            list[Middleware],
            Doc(
                """
                A list of middlewares to be applied to this *path operation*.
                """
            ),
        ],
    ):
        self.operations: list[OperationT] = []
        self.middlewares = middlewares or []
