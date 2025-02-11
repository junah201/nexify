from collections.abc import Callable, Sequence
from typing import (
    Annotated,
    Any,
    Literal,
)

from nexify import params, routing
from nexify.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    response_validation_exception_handler,
)
from nexify.exceptions import HTTPException, RequestValidationError, ResponseValidationError
from nexify.middleware import Middleware
from nexify.openapi.docs import get_swagger_ui_html
from nexify.openapi.utils import get_openapi
from nexify.responses import HttpResponse, JSONResponse
from nexify.schedule import ScheduleExpression, Scheduler
from nexify.types import ExceptionHandler, HandlerType, MiddlewareType
from typing_extensions import Doc


class Nexify:
    def __init__(
        self,
        *,
        debug: Annotated[
            bool,
            Doc(
                """
                Boolean indicating if debug tracebacks should be returned on server
                errors.
                """
            ),
        ] = False,
        title: Annotated[
            str,
            Doc(
                """
                The title of the API.

                It will be added to the generated OpenAPI.
                ```
                """
            ),
        ] = "Nexify API",
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
                A short summary of the API.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        description: Annotated[
            str,
            Doc(
                """
                A description of the API. Supports Markdown (using
                [CommonMark syntax](https://commonmark.org/)).

                It will be added to the generated OpenAPI.
                """
            ),
        ] = "",
        version: Annotated[
            str,
            Doc(
                """
                The version of the API.

                **Note** This is the version of your application, not the version of
                the OpenAPI specification nor the version of Nexify being used.

                It will be added to the generated OpenAPI.
                ```
                """
            ),
        ] = "0.1.0",
        openapi_tags: Annotated[
            list[dict[str, Any]] | None,
            # TODO: Fix the following docstring
            Doc(
                """
                A list of tags used by OpenAPI, these are the same `tags` you can set
                in the *path operations*, like:

                * `@app.get("/users/", tags=["users"])`
                * `@app.get("/items/", tags=["items"])`

                The order of the tags can be used to specify the order shown in
                tools like Swagger UI, used in the automatic path `/docs`.

                It's not required to specify all the tags used.

                The tags that are not declared MAY be organized randomly or based
                on the tools' logic. Each tag name in the list MUST be unique.

                The value of each item is a `dict` containing:

                * `name`: The name of the tag.
                * `description`: A short description of the tag.
                    [CommonMark syntax](https://commonmark.org/) MAY be used for rich
                    text representation.
                * `externalDocs`: Additional external documentation for this tag. If
                    provided, it would contain a `dict` with:
                    * `description`: A short description of the target documentation.
                        [CommonMark syntax](https://commonmark.org/) MAY be used for
                        rich text representation.
                    * `url`: The URL for the target documentation. Value MUST be in
                        the form of a URL.

                **Example**

                ```python
                tags_metadata = [
                    {
                        "name": "users",
                        "description": "Operations with users. The **login** logic is also here.",
                    },
                    {
                        "name": "items",
                        "description": "Manage items. So _fancy_ they have their own docs.",
                        "externalDocs": {
                            "description": "Items external docs",
                            "url": "https://nexify.junah.dev/",
                        },
                    },
                ]
                """
            ),
        ] = None,
        servers: Annotated[
            list[dict[str, str | Any]] | None,
            Doc(
                """
                A `list` of `dict`s with connectivity information to a target server.

                You would use it, for example, if your application is served from
                different domains and you want to use the same Swagger UI in the
                browser to interact with each of them (instead of having multiple
                browser tabs open). Or if you want to leave fixed the possible URLs.

                If the servers `list` is not provided, or is an empty `list`, the
                default value would be a `dict` with a `url` value of `/`.

                Each item in the `list` is a `dict` containing:

                * `url`: A URL to the target host. This URL supports Server Variables
                and MAY be relative, to indicate that the host location is relative
                to the location where the OpenAPI document is being served. Variable
                substitutions will be made when a variable is named in `{`brackets`}`.
                * `description`: An optional string describing the host designated by
                the URL. [CommonMark syntax](https://commonmark.org/) MAY be used for
                rich text representation.
                * `variables`: A `dict` between a variable name and its value. The value
                    is used for substitution in the server's URL template.

                **Example**

                ```python
                servers=[
                    {"url": "https://stag.example.com", "description": "Staging environment"},
                    {"url": "https://prod.example.com", "description": "Production environment"},
                ]
                ```
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
        terms_of_service: Annotated[
            str | None,
            Doc(
                """
                A URL to the Terms of Service for your API.

                It will be added to the generated OpenAPI.

                **Example**

                ```python
                app = Nexify(terms_of_service="http://example.com/terms")
                ```
                """
            ),
        ] = None,
        contact: Annotated[
            dict[str, str | Any] | None,
            Doc(
                """
                A dictionary with the contact information for the exposed API.

                It can contain several fields.

                * `name`: (`str`) The name of the contact person/organization.
                * `url`: (`str`) A URL pointing to the contact information. MUST be in
                    the format of a URL.
                * `email`: (`str`) The email address of the contact person/organization.
                    MUST be in the format of an email address.

                It will be added to the generated OpenAPI.

                **Example**

                ```python
                app = Nexify(
                    contact={
                        "name": "Deadpoolio the Amazing",
                        "url": "http://x-force.example.com/contact/",
                        "email": "dp@x-force.example.com",
                    }
                )
                ```
                """
            ),
        ] = None,
        license_info: Annotated[
            dict[str, str | Any] | None,
            Doc(
                """
                A dictionary with the license information for the exposed API.

                It can contain several fields.

                * `name`: (`str`) **REQUIRED** (if a `license_info` is set). The
                    license name used for the API.
                * `identifier`: (`str`) An [SPDX](https://spdx.dev/) license expression
                    for the API. The `identifier` field is mutually exclusive of the `url`
                    field. Available since OpenAPI 3.1.0.
                * `url`: (`str`) A URL to the license used for the API. This MUST be
                    the format of a URL.

                It will be added to the generated OpenAPI.

                **Example**

                ```python
                from nexify import Nexify

                app = Nexify(
                    license_info={
                        "name": "Apache 2.0",
                        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
                    }
                )
                ```
                """
            ),
        ] = None,
        root_path: Annotated[
            str,
            Doc(
                """
                A path prefix handled by a proxy that is not seen by the application
                but is seen by external clients, which affects things like Swagger UI.

                **Example**

                ```python
                from nexify import Nexify

                app = Nexify(root_path="/api/v1")
                ```
                """
            ),
        ] = "",
        deprecated: Annotated[
            bool | None,
            Doc(
                """
                Mark all *path operations* as deprecated. You probably don't need it,
                but it's available.

                It will be added to the generated OpenAPI.
                """
            ),
        ] = None,
        api_gateway_type: Annotated[
            Literal["rest", "http"],
            Doc(
                """
                The type of API Gateway to be used. It can be either `rest` or `http`.

                * `rest`: A REST API Gateway.
                * `http`: An HTTP API Gateway.

                **Example**

                ```python
                app = Nexify(api_gateway_type="rest")
                ```
                """
            ),
        ] = "rest",
        middlewares: Annotated[
            list[Middleware] | None,
            Doc(
                """
                A list of middlewares to be applied to this *path operation*.
                """
            ),
        ] = None,
    ):
        self.debug = debug
        self.title = title
        self.summary = summary
        self.description = description
        self.version = version
        self.openapi_tags = openapi_tags
        self.openapi_version = "3.1.0"
        self.openapi_schema: dict[str, Any] | None = None
        self.servers = servers or []
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.root_path = root_path
        self.deprecated = deprecated

        self.dependencies = list(dependencies or [])
        self.middlewares = middlewares or []
        self.router = routing.APIRouter(middlewares=self.middlewares)

        self.scheduler = Scheduler()

        self.exception_handlers: dict[
            type[Exception],
            ExceptionHandler,
        ] = exception_handlers or {}
        self.exception_handlers.setdefault(HTTPException, http_exception_handler)
        self.exception_handlers.setdefault(RequestValidationError, request_validation_exception_handler)
        self.exception_handlers.setdefault(ResponseValidationError, response_validation_exception_handler)

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
    ) -> Callable[[Callable], HandlerType]:
        """
        Add a net *path operation* to the AWS REST API.
        """
        return self.router.get(
            path=path,
            status_code=status_code,
            tags=tags,
            dependencies=self.dependencies + list(dependencies or []),
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=self.exception_handlers,
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
    ) -> Callable[[Callable], HandlerType]:
        """
        Add a net *path operation* to the AWS REST API.
        """
        return self.router.put(
            path=path,
            status_code=status_code,
            tags=tags,
            dependencies=self.dependencies + list(dependencies or []),
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=self.exception_handlers,
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
    ) -> Callable[[Callable], HandlerType]:
        """
        Add a net *path operation* to the AWS REST API.
        """
        return self.router.post(
            path=path,
            status_code=status_code,
            tags=tags,
            dependencies=self.dependencies + list(dependencies or []),
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=self.exception_handlers,
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
    ) -> Callable[[Callable], HandlerType]:
        """
        Add a net *path operation* to the AWS REST API.
        """
        return self.router.delete(
            path=path,
            status_code=status_code,
            tags=tags,
            dependencies=self.dependencies + list(dependencies or []),
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=self.exception_handlers,
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
    ) -> Callable[[Callable], HandlerType]:
        """
        Add a net *path operation* to the AWS REST API.
        """
        return self.router.options(
            path=path,
            status_code=status_code,
            tags=tags,
            dependencies=self.dependencies + list(dependencies or []),
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=self.exception_handlers,
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
    ) -> Callable[[Callable], HandlerType]:
        """
        Add a net *path operation* to the AWS REST API.
        """
        return self.router.head(
            path=path,
            status_code=status_code,
            tags=tags,
            dependencies=self.dependencies + list(dependencies or []),
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            operation_id=operation_id,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=self.exception_handlers,
        )

    def openapi(self) -> dict[str, Any]:
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                summary=self.summary,
                description=self.description,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
                routes=self.router.operations,
                tags=self.openapi_tags,
                servers=self.servers,
            )

        return self.openapi_schema

    def swagger_html(self) -> str:
        return get_swagger_ui_html(
            openapi_url="openapi.json",
            title=self.title,
        )

    def redoc_html(self) -> str:
        return get_swagger_ui_html(
            openapi_url="openapi.json",
            title=self.title,
        )

    def middleware(self, func: MiddlewareType) -> MiddlewareType:
        self.middlewares.insert(0, func)
        self.router.add_middleware(func)

        return func

    def add_middleware(self, middleware: MiddlewareType) -> None:
        self.middlewares.insert(0, middleware)
        self.router.add_middleware(middleware)

    def exception_handler(self, exception_class: type[Exception]):
        def decorator(func: ExceptionHandler) -> ExceptionHandler:
            self.exception_handlers[exception_class] = func
            return func

        return decorator

    def add_exception_handler(self, exception_class: type[Exception], handler: ExceptionHandler) -> None:
        self.exception_handlers[exception_class] = handler

    def schedule(self, expression: ScheduleExpression | list[ScheduleExpression]) -> Callable:
        if not isinstance(expression, list):
            expression = [expression]

        return self.scheduler.schedule(expressions=expression)
