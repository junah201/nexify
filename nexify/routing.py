import inspect
import re
import warnings
from collections.abc import Callable, Sequence
from re import Pattern
from typing import Annotated, Any, Literal, get_args

from nexify.convertors import CONVERTOR_TYPES, Convertor
from nexify.exceptions import RequestValidationError, ResponseValidationError
from nexify.models import ModelField, create_model_field
from nexify.params import Body, Context, Event, Path, Query
from nexify.responses import HttpResponse, JSONResponse
from nexify.types import ExceptionHandler, Handler
from nexify.utils import is_annotated
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined, PydanticUndefinedType
from typing_extensions import Doc

Undefined: Any = PydanticUndefined
UndefinedType: Any = PydanticUndefinedType


class Route:
    def __init__(
        self,
        path: str,
        endpoint: Callable,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ) -> None:
        assert path.startswith("/"), "Path must start with '/'"
        self.path = path
        self.endpoint = endpoint
        self.methods: set[Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]] = set(methods)
        self.status_code = status_code
        self.tags = tags or []
        self.summary = summary
        self.description = description
        self.response_description = response_description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.name = get_name(endpoint) if name is None else name
        self.openapi_extra = openapi_extra
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)
        self.unique_id = self.operation_id or generate_unique_id(self)

        self.body_fields, self.path_fields, self.query_fields, self.event_fields, self.context_fields = (
            self.get_fields()
        )
        self.fields = self.body_fields + self.path_fields + self.query_fields + self.event_fields + self.context_fields

        self.response_field = self.get_response_field()
        self.response_class = response_class

        self.exception_handlers = exception_handlers or {}

    def get_fields(
        self,
    ) -> tuple[list[ModelField], list[ModelField], list[ModelField], list[ModelField], list[ModelField]]:
        body_fields: list[ModelField] = []
        path_fields: list[ModelField] = []
        query_fields: list[ModelField] = []
        event_fields: list[ModelField] = []
        context_fields: list[ModelField] = []

        signature = inspect.signature(self.endpoint)

        for name, param in signature.parameters.items():
            annotation = param.annotation

            if not is_annotated(annotation):
                warnings.warn(
                    f"Parameter {name} is not annotated. Skipping parsing.",
                    stacklevel=2,
                )
                continue

            base_type, param_type, *_ = get_args(annotation)
            param_default = param.default if param.default != param.empty else Undefined
            default_value = (
                param.default if param.default != param.empty else param_type.get_default(call_default_factory=True)
            )
            assert default_value is Undefined or isinstance(default_value, base_type), (
                f"Default value {default_value} is not an instance of {base_type}"
            )

            if isinstance(param_type, Event | Context | Path):
                assert default_value is Undefined, f"{param_type} parameter must do not have default values"

            assert isinstance(param_type, Path | Query | Body | Event | Context), (
                f"Unsupported metadata type {param_type}. Must be Path, Query, Body, Event, or Context"
            )

            assert issubclass(base_type, str | int | float | bool | dict | BaseModel), (
                "Parameters must be annotated with str, int, float, bool, dict, or pydantic BaseModel"
            )

            if isinstance(param_type, Path):
                assert self.path.count("{" + name + "}") == 1, f"Path parameter {name} is not present in {self.path}"

            param_type.validate_annotation(base_type)
            param_type.alias = param_type.alias or name
            param_type.annotation = base_type
            if param_default is not Undefined:
                assert param_type.get_default(call_default_factory=True) == Undefined, "Default value is already set"
                param_type.default = default_value

            field = ModelField(name=name, field_info=param_type, mode="validation")

            if isinstance(param_type, Body):
                body_fields.append(field)
            elif isinstance(param_type, Path):
                path_fields.append(field)
            elif isinstance(param_type, Query):
                query_fields.append(field)
            elif isinstance(param_type, Event):
                event_fields.append(field)
            elif isinstance(param_type, Context):
                context_fields.append(field)

        return body_fields, path_fields, query_fields, event_fields, context_fields

    def get_response_field(self):
        response_model = self.endpoint.__annotations__.get("return", Undefined)

        if response_model is Undefined:
            return None

        name = f"{self.endpoint.__name__}_response"
        return create_model_field(
            FieldInfo(
                name=name,
            ),
            annotation=response_model,
            name=name,
        )

    def process_input(self, event, _context) -> dict[str, Any]:
        parsed_data = {}
        errors = []

        for field in self.fields:
            source = field.field_info.get_source(event, _context)
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

        return parsed_data

    def execute_handler(self, parsed_data: dict[str, Any]):
        content = self.endpoint(**parsed_data)
        if self.response_field:
            content, _errors = self.response_field.validate(content, loc=("response",))  # type: ignore

            if _errors:
                raise ResponseValidationError(_errors, body=content)

        if isinstance(content, HttpResponse):
            response = content
        else:
            response = self.response_class(content=content, status_code=self.status_code)

        return response.render()

    def handle_request(self, event, _context):
        parsed_data = self.process_input(event, _context)
        return self.execute_handler(parsed_data)

    def __call__(self, event, _context):
        try:
            return self.handle_request(event, _context)
        except Exception as e:
            for exception, handler in self.exception_handlers.items():
                if isinstance(e, exception):
                    res = handler(event, _context, e)
                    return res.render()
            raise e


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
        self.routes: list[Route] = []

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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
            Doc(
                """
                A dictionary with handlers for exceptions.
                """
            ),
        ] = None,
    ) -> Callable[[Callable], Handler]:
        def decorator(func: Callable) -> Handler:
            route = self.create_route(
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
                response_class=response_class,
                name=name,
                openapi_extra=openapi_extra,
                exception_handlers=exception_handlers,
            )
            self.routes.append(route)
            return route

        return decorator

    def create_route(
        self,
        path: str,
        endpoint: Handler,
        *,
        methods: Sequence[Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]] = ["GET"],
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        deprecated: bool | None = None,
        operation_id: str | None = None,
        response_class: type[HttpResponse] = JSONResponse,
        name: str | None = None,
        openapi_extra: dict[str, Any] | None = None,
        exception_handlers: dict[
            int | type[Exception],
            ExceptionHandler,
        ]
        | None = None,
    ) -> Route:
        return Route(
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
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
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
            dict[
                int | type[Exception],
                ExceptionHandler,
            ]
            | None,
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
            summary=summary,
            description=description,
            response_description=response_description,
            deprecated=deprecated,
            response_class=response_class,
            name=name,
            openapi_extra=openapi_extra,
            exception_handlers=exception_handlers,
        )


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


def get_name(endpoint: Handler) -> str:
    return getattr(endpoint, "__name__", endpoint.__class__.__name__)
