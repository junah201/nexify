from collections.abc import Callable, Sequence
from functools import wraps
from typing import Annotated, Any

from nexify.parser import handler_validation, parse_data
from nexify.types import Handler
from typing_extensions import Doc


class Route:
    def __init__(
        self,
        path: str,
        endpoint: Handler,
        *,
        methods: Annotated[
            Sequence[str],
            Doc(
                """
                The HTTP methods to be used for this *path operation*.

                For example, `["GET", "POST"]`.
                """
            ),
        ] = "GET",
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
    ) -> None:
        assert path.startswith("/"), "Path must start with '/'"
        self.path = path
        self.endpoint = endpoint
        if methods is None:
            methods = ["GET"]

        self.methods = {method.upper() for method in methods}
        if "GET" in self.methods:
            self.methods.add("HEAD")


class APIRouter:
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
    ):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: list = []

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
            Sequence[str],
            Doc(
                """
                The HTTP methods to be used for this *path operation*.

                For example, `["GET", "POST"]`.
                """
            ),
        ] = "GET",
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
    ) -> Callable[[Callable], Handler]:
        def decorator(func: Callable) -> Handler:
            handler_validation(func, path)
            self.add_route(
                path,
                func,
                methods=methods,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                deprecated=deprecated,
                operation_id=operation_id,
                name=name,
                openapi_extra=openapi_extra,
            )

            @wraps(func)
            def wrapper(event, _context):
                parsed_data = parse_data(func, path, event, _context)
                return func(**parsed_data)

            return wrapper

        return decorator

    def add_route(
        self,
        path: str,
        endpoint: Handler,
        *,
        methods: Sequence[str] = "GET",
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        deprecated: bool | None = None,
        operation_id: str | None = None,
        name: str | None = None,
        openapi_extra: dict[str, Any] | None = None,
    ):
        self.routes.append(
            Route(
                path=self.prefix + path,
                endpoint=endpoint,
                methods=methods,
                status_code=status_code,
                tags=tags,
                summary=summary,
                description=description,
                response_description=response_description,
                deprecated=deprecated,
                operation_id=operation_id,
                name=name,
                openapi_extra=openapi_extra,
            )
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
        methods: Annotated[
            Sequence[str],
            Doc(
                """
                The HTTP methods to be used for this *path operation*.

                For example, `["GET", "POST"]`.
                """
            ),
        ] = "GET",
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
    ):
        return self.route(
            path=self.prefix + path,
            methods=methods,
            status_code=status_code,
            tags=tags,
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            name=name,
            openapi_extra=openapi_extra,
        )
