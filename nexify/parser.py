import inspect
import json
import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, get_args

from nexify.openapi.models import ModelField
from nexify.params import Body, Context, Event, FieldType, Path, Query
from nexify.utils import is_annotated
from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

if TYPE_CHECKING:
    from nexify.routing import Route


Undefined: Any = PydanticUndefined


def parse_data(func: Callable, path: str, event: dict, context: dict) -> dict[str, Any]:  # noqa: ARG001
    """
    Parse the event and context from the AWS Lambda handler
    """

    signature = inspect.signature(func)
    parsed_data: dict[str, Any] = {}

    for name, param in signature.parameters.items():
        annotation = param.annotation

        if not is_annotated(annotation):
            warnings.warn(
                f"Parameter {name} is not annotated. Skipping parsing.",
                stacklevel=2,
            )
            continue

        base_type, param_type, *_ = get_args(annotation)
        default_value = (
            param.default if param.default != param.empty else param_type.get_default(call_default_factory=True)
        )

        if isinstance(param_type, Event):
            assert issubclass(base_type, dict), "Event parameter must be a dictionary"
            assert default_value is Undefined, "Event parameter must do not have default values"
            parsed_data[name] = event
            continue

        if isinstance(param_type, Context):
            assert issubclass(base_type, dict), "Context parameter must be a dictionary"
            assert default_value is Undefined, "Context parameter must do not have default values"
            parsed_data[name] = context
            continue

        assert isinstance(param_type, Path | Query | Body), (
            f"Unsupported metadata type {param_type}. Must be Path, Query, or Body"
        )

        assert issubclass(base_type, str | int | float | bool | dict | BaseModel), (
            "Parameters must be annotated with str, int, float, bool, dict, or pydantic BaseModel"
        )

        if isinstance(param_type, Path):
            assert issubclass(base_type, str | int | float | bool), (
                "Path parameters must be annotated with str, int, float, or bool"
            )

        if isinstance(param_type, Query):
            assert issubclass(base_type, str | int | float | bool), (
                "Query parameters must be annotated with str, int, float, or bool"
            )

        if isinstance(param_type, Body):
            assert issubclass(base_type, dict | BaseModel), (
                "Body parameters must be annotated with a dict or pydantic BaseModel"
            )

        if isinstance(param_type, Path):
            source = event.get("pathParameters", {})
        elif isinstance(param_type, Query):
            source = event.get("queryStringParameters", {})
        elif isinstance(param_type, Body):
            source = event.get("body", "{}")

        if isinstance(param_type, Path):
            assert default_value is Undefined, "Path parameters cannot have default values"

        assert default_value is Undefined or isinstance(default_value, base_type), (
            f"Default value {default_value} is not an instance of {base_type}"
        )
        assert isinstance(param_type, Body) or not (
            source.get(name, Undefined) is Undefined and default_value is Undefined
        ), f"Missing parameter {name} in {path}"

        if isinstance(param_type, Body):
            try:
                if issubclass(base_type, BaseModel):
                    parsed_data[name] = base_type.model_validate_json(source)
                    continue
                elif issubclass(base_type, dict):
                    value = json.loads(source)
                    assert not (not value and default_value is Undefined), f"Missing body {name} in {path}"
                    assert isinstance(default_value, dict) or default_value is Undefined
                    assert default_value is Undefined or isinstance(default_value, dict)
                    if default_value is not Undefined:
                        value = default_value if not value else value
                    parsed_data[name] = value
                    continue
            except ValidationError as e:
                raise ValueError(f"Failed to parse parameter {name} in {path}") from e

        value = source.get(name, Undefined) if source.get(name, Undefined) is not Undefined else default_value

        if issubclass(base_type, bool):
            assert isinstance(value, str), f"Parameter {name} must be a string"
            parsed_data[name] = value.lower() == "true" or value.lower() == "1"
            continue

        try:
            data = base_type(value)  # type: ignore
        except TypeError:
            raise TypeError(f"Failed to parse parameter {name} in {path}")
        except ValueError:
            raise ValueError(f"Failed to parse parameter {name} in {path}")
        assert isinstance(data, base_type), f"Parameter {name} must be an instance of {base_type}"

        parsed_data[name] = data

    parsed_data = {k: v for k, v in parsed_data.items() if v is not Undefined}

    return parsed_data


def handler_validation(func: Callable, path: str):
    """
    Validate the handler function
    """

    signature = inspect.signature(func)

    for name, param in signature.parameters.items():
        annotation = param.annotation

        if not is_annotated(annotation):
            warnings.warn(
                f"Parameter {name} is not annotated. Skipping parsing.",
                stacklevel=2,
            )
            continue

        base_type, param_type, *_ = get_args(annotation)
        default_value = (
            param.default if param.default != param.empty else param_type.get_default(call_default_factory=True)
        )

        if isinstance(param_type, Event):
            assert issubclass(base_type, dict), "Event parameter must be a dictionary"
            assert default_value is Undefined, "Event parameter must do not have default values"
            continue

        if isinstance(param_type, Context):
            assert issubclass(base_type, dict), "Context parameter must be a dictionary"
            assert default_value is Undefined, "Context parameter must do not have default values"
            continue

        assert isinstance(param_type, Path | Query | Body), (
            f"Unsupported metadata type {param_type}. Must be Path, Query, or Body"
        )

        assert issubclass(base_type, str | int | float | bool | dict | BaseModel), (
            "Parameters must be annotated with str, int, float, bool, dict, or pydantic BaseModel"
        )

        if isinstance(param_type, Path):
            assert issubclass(base_type, str | int | float | bool), (
                "Path parameters must be annotated with str, int, float, or bool"
            )
            assert path.count("{" + name + "}") == 1, f"Path parameter {name} is not present in {path}"

        if isinstance(param_type, Query):
            assert issubclass(base_type, str | int | float | bool), (
                "Query parameters must be annotated with str, int, float, or bool"
            )

        if isinstance(param_type, Body):
            assert issubclass(base_type, dict | BaseModel), (
                "Body parameters must be annotated with a dict or pydantic BaseModel"
            )

        if isinstance(param_type, Path):
            assert default_value is Undefined, "Path parameters cannot have default values"

        assert default_value is Undefined or isinstance(default_value, base_type), (
            f"Default value {default_value} is not an instance of {base_type}"
        )


def params_fields(route: "Route", field_type: FieldType | None = None) -> list[ModelField]:
    """
    Get the fields from the route
    """
    fields: list[ModelField] = []

    signature = inspect.signature(route.endpoint)

    for name, param in signature.parameters.items():
        annotation = param.annotation

        if not is_annotated(annotation):
            continue

        base_type, param_type, *_ = get_args(annotation)

        if isinstance(param_type, Event | Context):
            continue

        if field_type is not None and not isinstance(param_type, field_type):
            continue

        param_type.annotation = base_type
        field = ModelField(name=name, field_info=param_type, mode="validation")
        fields.append(field)

    return fields
