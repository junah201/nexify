import warnings
from collections.abc import Sequence
from itertools import chain
from typing import Any, Literal, cast

from nexify.encoders import jsonable_encoder
from nexify.models import ModelField
from nexify.openapi.constants import METHODS_WITH_BODY, REF_TEMPLATE
from nexify.params import Body, ParamTypes
from nexify.routing import Route
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import PydanticUndefined

Undefined: Any = PydanticUndefined


def get_openapi(
    *,
    title: str,
    version: str,
    openapi_version: str = "3.1.0",
    summary: str | None = None,
    description: str | None = None,
    routes: Sequence[Route],
    tags: list[dict[str, Any]] | None = None,
    servers: list[dict[str, str | Any]] | None = None,
    terms_of_service: str | None = None,
    contact: dict[str, str | Any] | None = None,
    license_info: dict[str, str | Any] | None = None,
) -> dict[str, Any]:
    info: dict[str, Any] = {
        "title": title,
        "version": version,
    }
    info_extra = {
        "summary": summary,
        "description": description,
        "termsOfService": terms_of_service,
        "contact": contact,
        "license": license_info,
    }
    info.update({k: v for k, v in info_extra.items() if v is not None})

    output = {
        "openapi": openapi_version,
        "info": info,
    }
    output_extra = {
        "servers": servers,
        "tags": tags,
    }
    output.update({k: v for k, v in output_extra.items() if v is not None})

    components: dict[str, dict[str, Any]] = {}
    paths: dict[str, dict[str, Any]] = {}
    operation_ids: set[str] = set()
    all_fields = list(chain.from_iterable(route.fields for route in list(routes or [])))
    schema_generator = GenerateJsonSchema(ref_template=REF_TEMPLATE)
    field_mapping, definitions = get_definitions(
        fields=all_fields,
        schema_generator=schema_generator,
    )
    for route in list(routes or []):
        result = get_openapi_path(
            route=route,
            operation_ids=operation_ids,
            field_mapping=field_mapping,
        )

        if not result:
            continue

        path, security_schemes, path_definitions = result
        if path:
            paths.setdefault(route.path, {}).update(path)
        if security_schemes:
            components.setdefault("securitySchemes", {}).update(security_schemes)
        if path_definitions:
            definitions.update(path_definitions)

    if definitions:
        components["schemas"] = {k: definitions[k] for k in sorted(definitions)}
    if components:
        output["components"] = components
    output["paths"] = paths
    if tags:
        output["tags"] = tags

    return output


def get_openapi_path(
    *,
    route: Route,
    operation_ids: set[str],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    path = {}
    security_schemes: dict[str, Any] = {}
    definitions: dict[str, Any] = {}
    assert route.methods is not None, "Methods must be a list"

    for method in route.methods:
        operation = get_openapi_operation_metadata(route=route, operation_ids=operation_ids)
        parameters: list[dict[str, Any]] = []
        operation_parameters = _get_openapi_operation_parameters(
            route=route,
            field_mapping=field_mapping,
        )
        parameters.extend(operation_parameters)
        if parameters:
            all_parameters = {(param["in"], param["name"]): param for param in parameters}
            required_parameters = {(param["in"], param["name"]): param for param in parameters if param.get("required")}
            # Make sure required definitions of the same parameter take precedence
            # over non-required definitions
            all_parameters.update(required_parameters)
            operation["parameters"] = list(all_parameters.values())
        if method in METHODS_WITH_BODY:
            request_body_oai = get_openapi_operation_request_body(
                body_fields=route.body_fields,
                field_mapping=field_mapping,
            )
            if request_body_oai:
                operation["requestBody"] = request_body_oai

        if route.openapi_extra:
            deep_dict_update(operation, route.openapi_extra)
        path[method.lower()] = operation

    return path, security_schemes, definitions


def _get_openapi_operation_parameters(
    *,
    route: Route,
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> list[dict[str, Any]]:
    parameters = []
    path_fields = route.path_fields
    query_fields = route.query_fields
    parameter_groups = [
        (ParamTypes.path, path_fields),
        (ParamTypes.query, query_fields),
    ]
    for param_type, param_group in parameter_groups:
        for param in param_group:
            field_info = param.field_info
            if not getattr(field_info, "include_in_schema", True):
                continue
            param_schema = get_schema_from_model_field(
                field=param,
                field_mapping=field_mapping,
            )
            parameter = {
                "name": param.alias,
                "in": param_type.value,
                "required": param.required,
                "schema": param_schema,
            }
            if field_info.description:
                parameter["description"] = field_info.description
            openapi_examples = getattr(field_info, "openapi_examples", None)
            if openapi_examples:
                parameter["examples"] = jsonable_encoder(openapi_examples)
            if getattr(field_info, "deprecated", None):
                parameter["deprecated"] = True
            parameters.append(parameter)
    return parameters


def get_schema_from_model_field(
    *,
    field: ModelField,
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> dict[str, Any]:
    # override_mode: Union[Literal["validation"], None] = None if separate_input_output_schemas else "validation"
    json_schema = field_mapping[(field, field.mode)]
    return json_schema


def get_openapi_operation_request_body(
    *,
    body_fields: list[ModelField],
    field_mapping: dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
) -> dict[str, Any] | None:
    if not body_fields:
        return None
    body_field = body_fields[0]
    assert isinstance(body_field, ModelField)
    body_schema = get_schema_from_model_field(
        field=body_field,
        field_mapping=field_mapping,
    )
    field_info = cast(Body, body_field.field_info)
    request_media_type = field_info.media_type
    required = body_field.required
    request_body_oai: dict[str, Any] = {}
    if required:
        request_body_oai["required"] = required
    request_media_content: dict[str, Any] = {"schema": body_schema}
    if field_info.openapi_examples:
        request_media_content["examples"] = jsonable_encoder(field_info.openapi_examples)
    request_body_oai["content"] = {request_media_type: request_media_content}
    return request_body_oai


def generate_operation_summary(*, route: Route) -> str:
    if route.summary:
        return route.summary
    return route.name.replace("_", " ").title()


def get_openapi_operation_metadata(*, route: Route, operation_ids: set[str]) -> dict[str, Any]:
    operation: dict[str, Any] = {}
    if route.tags:
        operation["tags"] = route.tags
    operation["summary"] = generate_operation_summary(route=route)
    if route.description:
        operation["description"] = route.description
    operation_id = route.operation_id or route.unique_id
    if operation_id in operation_ids:
        message = f"Duplicate Operation ID {operation_id} for function " + f"{route.endpoint.__name__}"
        file_name = getattr(route.endpoint, "__globals__", {}).get("__file__")
        if file_name:
            message += f" at {file_name}"
        warnings.warn(message, stacklevel=1)
    operation_ids.add(operation_id)
    operation["operationId"] = operation_id
    if route.deprecated:
        operation["deprecated"] = route.deprecated
    return operation


def get_fields_from_routes(routes: list[Route]) -> list[ModelField]:
    model_fields: list[ModelField] = []

    for route in routes:
        fields = route.fields
        model_fields.extend(fields)

    return model_fields


def get_definitions(
    *,
    fields: list[ModelField],
    schema_generator: GenerateJsonSchema,
) -> tuple[
    dict[tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    dict[str, dict[str, Any]],
]:
    # override_mode: Literal["validation"] | None = None if separate_input_output_schemas else "validation"
    inputs = [(field, field.mode, field._type_adapter.core_schema) for field in fields]
    field_mapping, definitions = schema_generator.generate_definitions(
        inputs=inputs  # type: ignore[arg-type]
    )
    return field_mapping, definitions  # type: ignore[return-value]


def deep_dict_update(main_dict: dict[Any, Any], update_dict: dict[Any, Any]) -> None:
    for key, value in update_dict.items():
        if key in main_dict and isinstance(main_dict[key], dict) and isinstance(value, dict):
            deep_dict_update(main_dict[key], value)
        elif key in main_dict and isinstance(main_dict[key], list) and isinstance(update_dict[key], list):
            main_dict[key].extend(value)
        else:
            main_dict[key] = value
