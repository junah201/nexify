import json
import re
from collections.abc import Callable, Sequence
from functools import wraps
from re import Pattern
from typing import Annotated, Any

from pydantic import ValidationError

from nexify.convertors import CONVERTOR_TYPES, Convertor
from nexify.openapi.models import ModelField
from nexify.params import Body, Context, Event, FieldType, Path, Query
from nexify.parser import handler_validation, params_fields, parse_data
from nexify.types import Handler
from typing_extensions import Doc


class Route:
    def __init__(
        self,
        path: str,
        endpoint: Callable,
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

        _tmp_body_field = self._get_specific_fields(Body)
        self.body_field = _tmp_body_field[0] if _tmp_body_field else None
        self.path_fields = self._get_specific_fields(Path)
        self.query_fields = self._get_specific_fields(Query)
        _tmp_event_field = self._get_specific_fields(Event)
        self.event_field = _tmp_event_field[0] if _tmp_event_field else None
        _tmp_context_field = self._get_specific_fields(Context)
        self.context_field = _tmp_context_field[0] if _tmp_context_field else None
        self.fields = self.get_all_fields()

        self.response = self.get_return_type()

    def _get_specific_fields(self, field_type: FieldType) -> list[ModelField]:
        fields = params_fields(self, field_type=field_type)
        return fields

    def get_all_fields(self) -> list[ModelField]:
        fields = []
        if self.body_field:
            fields.append(self.body_field)
        fields.extend(self.path_fields)
        fields.extend(self.query_fields)
        if self.event_field:
            fields.append(self.event_field)
        if self.context_field:
            fields.append(self.context_field)

        return fields

    def get_return_type(self) -> Any:
        print(self.endpoint.__annotations__.get("return", None))
        return self.endpoint.__annotations__.get("return", None)

    def __call__(self, event, _context):
        parsed_data = parse_data(self.endpoint, self.path, event, _context)
        try:
            body = self.endpoint(**parsed_data)
            res = {
                "statusCode": self.status_code or 200,
                "body": json.dumps(body),
            }
        except ValidationError as e:
            res = {
                "statusCode": 422,
                "body": json.dumps(
                    {
                        "detail": "Bad Request",
                        "errors": e.errors(),
                    }
                ),
            }
        except Exception:
            res = {
                "statusCode": 500,
                "body": json.dumps(
                    {
                        "detail": "Internal Server Error",
                    }
                ),
            }

        return res


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
                name=name,
                openapi_extra=openapi_extra,
            )
            self.routes.append(route)
            return route

        return decorator

    def create_route(
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
            name=name,
            openapi_extra=openapi_extra,
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


def generate_operation_summary(*, route: Route, method: str) -> str:
    if route.summary:
        return route.summary
    return route.name.replace("_", " ").title()


def get_name(endpoint: Handler) -> str:
    return getattr(endpoint, "__name__", endpoint.__class__.__name__)
