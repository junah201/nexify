import inspect
import warnings
from collections.abc import Callable
from typing import Any, get_args

from nexify.params import Body, Context, Event, Path, Query
from nexify.utils import is_annotated
from pydantic import BaseModel, ValidationError


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

        if isinstance(param_type, Event):
            parsed_data[name] = event
            continue

        if isinstance(param_type, Context):
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
            source = event.get("pathParameters", "{}")
        elif isinstance(param_type, Query):
            source = event.get("queryStringParameters", "{}")
        elif isinstance(param_type, Body):
            source = event.get("body", "{}")

        assert source.get(name, None) is not None, f"Missing parameter {name} in {path}"

        try:
            if issubclass(base_type, str):
                parsed_data[name] = source.get(name)
            elif issubclass(base_type, int):
                parsed_data[name] = int(source.get(name))
            elif issubclass(base_type, float):
                parsed_data[name] = float(source.get(name))
            elif issubclass(base_type, bool):
                parsed_data[name] = source.get(name).lower() == "true" or source.get(name) == "1"
            elif issubclass(base_type, dict):
                data = source.get(name)
                assert isinstance(data, dict), f"Parameter {name} must be a dictionary"
                parsed_data[name] = data
        except TypeError:
            raise TypeError(f"Failed to parse parameter {name} in {path}")
        except ValueError:
            raise ValueError(f"Failed to parse parameter {name} in {path}")

        try:
            if issubclass(base_type, BaseModel):
                parsed_data[name] = base_type.model_validate_json(source)
        except ValidationError as e:
            raise ValueError(f"Failed to parse parameter {name} in {path}") from e

    return parsed_data
