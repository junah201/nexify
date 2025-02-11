import re
from collections.abc import Callable, Sequence
from re import Pattern
from typing import Annotated, Any, Literal

from nexify import params
from nexify.convertors import CONVERTOR_TYPES, Convertor
from nexify.dependencies.utils import get_dependant, get_sub_dependant, get_typed_return_annotation
from nexify.middleware import (
    ExceptionMiddleware,
    Middleware,
    RenderMiddleware,
    RequestParsingMiddleware,
    ResponseValidationMiddleware,
    ServerErrorMiddleware,
)
from nexify.models import create_model_field
from nexify.operation import Operation, OperationManager
from nexify.responses import HttpResponse, JSONResponse
from nexify.types import ExceptionHandler, HandlerType, MiddlewareType
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined, PydanticUndefinedType
from typing_extensions import Doc

Undefined: Any = PydanticUndefined
UndefinedType: Any = PydanticUndefinedType


class Route(Operation):
    def __init__(
        self,
        path: str,
        handler: Callable,
        *,
        methods: Annotated[
            Sequence[Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]],
            Doc(
                """
                The HTTP methods to be used for this *path operation*.

                For example, `["GET", "POST"]`.
                """
            ),
        ],
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        middlewares: Annotated[
            list[Middleware] | None,
            Doc(
                """
                A list of middlewares to be applied to this *path operation*.
                """
            ),
        ] = None,
    ) -> None:
        assert path.startswith("/"), "Path must start with '/'"
        super().__init__(handler=handler, middlewares=middlewares)

        self.path = path
        self.methods: set[Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]] = set(methods)
        self.status_code = status_code
        self.dependencies = list(dependencies or [])
        self.tags = tags or []
        self.summary = summary
        self.description = description
        self.response_description = response_description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.name = get_name(handler) if name is None else name
        self.openapi_extra = openapi_extra
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)
        self.unique_id = self.operation_id or generate_unique_id(self)

        self.dependant = get_dependant(
            path=self.path_format,
            call=self.handler,
        )
        for depends in reversed(self.dependencies):
            self.dependant.dependencies.insert(
                0,
                get_sub_dependant(
                    depends=depends,
                    dependency=depends.dependency,
                    path=self.path_format,
                ),
            )

        return_annotation = get_typed_return_annotation(self.handler)
        if return_annotation is not None:
            _name = f"{self.handler.__name__}_response"
            self.response_field = create_model_field(
                FieldInfo(
                    name=_name,
                ),
                annotation=return_annotation,
                name=_name,
            )
        else:
            self.response_field = None
        self.response_class = response_class


class APIRouter(OperationManager[Route]):
    def __init__(
        self,
        *,
        prefix: Annotated[str, Doc("An optional path prefix for this router.")] = "",
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to all the *path operations* in this
                router.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        middlewares: Annotated[
            list[Middleware] | None,
            Doc(
                """
                A list of middlewares to be applied to this *path operation*.
                """
            ),
        ] = None,
    ):
        super().__init__(middlewares=middlewares or [])
        self.prefix = prefix
        self.tags = tags or []

    def route(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        methods: Annotated[
            Sequence[Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]],
            Doc(
                """
                The HTTP methods to be used for this *path operation*.

                For example, `["GET", "POST"]`.
                """
            ),
        ],
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ) -> Callable[[Callable], HandlerType]:
        def decorator(func: Callable) -> HandlerType:
            route = self.create_route(
                path,
                func,
                methods=methods,
                status_code=status_code,
                tags=tags,
                dependencies=dependencies,
                summary=summary,
                description=description,
                response_description=response_description,
                deprecated=deprecated,
                operation_id=operation_id,
                response_class=response_class,
                name=name,
                openapi_extra=openapi_extra,
                exception_handlers=exception_handlers,
            )
            self.operations.append(route)
            return route

        return decorator

    def create_route(
        self,
        path: str,
        endpoint: HandlerType,
        *,
        methods: Sequence[Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]] = ["GET"],
        status_code: int | None = None,
        tags: list[str] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        deprecated: bool | None = None,
        operation_id: str | None = None,
        response_class: type[HttpResponse] = JSONResponse,
        name: str | None = None,
        openapi_extra: dict[str, Any] | None = None,
        exception_handlers: dict[type[Exception], ExceptionHandler] | None = None,
    ) -> Route:
        middlewares = (
            [
                RenderMiddleware(),
                ServerErrorMiddleware(),
                ExceptionMiddleware(exception_handlers or {}),
                ResponseValidationMiddleware(),
            ]
            + self.middlewares
            + [RequestParsingMiddleware()]
        )
        return Route(
            path=self.prefix + path,
            handler=endpoint,
            methods=methods,
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            middlewares=middlewares,
        )

    def get(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ):
        return self.route(
            path=self.prefix + path,
            methods=["GET"],
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )

    def put(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ):
        return self.route(
            path=self.prefix + path,
            methods=["PUT"],
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )

    def post(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ):
        return self.route(
            path=self.prefix + path,
            methods=["POST"],
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )

    def delete(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ):
        return self.route(
            path=self.prefix + path,
            methods=["DELETE"],
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )

    def head(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ):
        return self.route(
            path=self.prefix + path,
            methods=["OPTIONS"],
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )

    def options(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        *,
        status_code: Annotated[
            int | None,
            Doc(
                """
                The status code to be used for this *path operation*.

                For example, in `http://example.com/items`, the status code is `200`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        dependencies: Annotated[
            Sequence[params.Depends] | None,
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied
                """
            ),
        ] = None,
        summary: Annotated[
            str | None,
            Doc(
                """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        response_description: Annotated[
            str,
            Doc(
                """
                The description for the default response.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "Successful Response",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        operation_id: Annotated[
            str | None,
            Doc(
                """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `Nexify` class.
                """
            ),
        ] = None,
        response_class: Annotated[
            type[HttpResponse],
            Doc(
                """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.
                """
            ),
        ] = JSONResponse,
        name: Annotated[
            str | None,
            Doc(
                """
                Name for this *path operation*. Only used internally.
                """
            ),
        ] = None,
        openapi_extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.
                """
            ),
        ] = None,
        exception_handlers: Annotated[
            dict[type[Exception], ExceptionHandler] | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ):
        return self.route(
            path=self.prefix + path,
            methods=["HEAD"],
            status_code=status_code,
            tags=tags,
            dependencies=dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )

    def add_middleware(self, middleware: MiddlewareType):
        self.middlewares.insert(0, middleware)


# Match parameters in URL paths, eg. '{param}', and '{param:int}'
PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")


def compile_path(
    path: str,
) -> tuple[Pattern[str], str, dict[str, Convertor[Any]]]:
    """
    Given a path string, like: "/{username:str}",
    or a host string, like: "{subdomain}.mydomain.org", return a three-tuple
    of (regex, format, {param_name:convertor}).

    regex:      "/(?P<username>[^/]+)"
    format:     "/{username}"
    convertors: {"username": StringConvertor()}
    """
    is_host = not path.startswith("/")

    path_regex = "^"
    path_format = ""
    duplicated_params = set()

    idx = 0
    param_convertors = {}
    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_type = match.groups("str")
        convertor_type = convertor_type.lstrip(":")
        assert convertor_type in CONVERTOR_TYPES, f"Unknown path convertor '{convertor_type}'"
        convertor = CONVERTOR_TYPES[convertor_type]

        path_regex += re.escape(path[idx : match.start()])
        path_regex += f"(?P<{param_name}>{convertor.regex})"

        path_format += path[idx : match.start()]
        path_format += f"{{{param_name}}}"

        if param_name in param_convertors:
            duplicated_params.add(param_name)

        param_convertors[param_name] = convertor

        idx = match.end()

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    if is_host:
        # Align with `Host.matches()` behavior, which ignores port.
        hostname = path[idx:].split(":")[0]
        path_regex += re.escape(hostname) + "$"
    else:
        path_regex += re.escape(path[idx:]) + "$"

    path_format += path[idx:]

    return re.compile(path_regex), path_format, param_convertors


def generate_unique_id(route: Route) -> str:
    operation_id = f"{route.name}{route.path_format}"
    operation_id = re.sub(r"\W", "_", operation_id)
    assert route.methods
    operation_id = f"{operation_id}_{list(route.methods)[0].lower()}"
    return operation_id


def get_name(endpoint: HandlerType) -> str:
    return getattr(endpoint, "__name__", endpoint.__class__.__name__)
