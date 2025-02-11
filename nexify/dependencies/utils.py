import copy
import inspect
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, get_args

from nexify import params
from nexify.dependencies.models import Dependant
from nexify.models import ModelField, create_model_field
from nexify.utils import is_annotated
from pydantic._internal._typing_extra import try_eval_type


def get_typed_annotation(annotation: Any, globalns: dict[str, Any]) -> Any:
    if isinstance(annotation, str):
        annotation = try_eval_type(annotation, globalns, globalns)
    return annotation


def get_typed_return_annotation(call: Callable[..., Any]) -> Any:
    signature = inspect.signature(call)
    annotation = signature.return_annotation

    if annotation is inspect.Signature.empty:
        return None

    globalns = getattr(call, "__globals__", {})
    return get_typed_annotation(annotation, globalns)


def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]
    typed_signature = inspect.Signature(typed_params)
    return typed_signature


@dataclass
class ParamDetails:
    type_annotation: Any
    depends: params.Depends | None
    field: ModelField | None


def analyze_param(
    *,
    param_name: str,
    annotation: Any,
    value: Any,
) -> ParamDetails:
    field = None
    depends = None

    annotated_args = get_args(annotation)
    type_annotation = annotated_args[0]  # e.g. Annotated[str, Query(...)] -> str
    base_annotation = annotated_args[1]  # e.g. Annotated[str, Query(...)] -> Query(...)

    if isinstance(base_annotation, params.Depends):
        depends = base_annotation
    else:
        field_info = copy.deepcopy(base_annotation)
        field = create_model_field(
            field_info=field_info,
            annotation=type_annotation,
            name=param_name,
            default=value,
        )

    return ParamDetails(
        type_annotation=type_annotation,
        depends=depends,
        field=field,
    )


def get_param_sub_dependant(
    *,
    param_name: str,
    depends: params.Depends,
    path: str,
) -> Dependant:
    assert depends.dependency
    return get_sub_dependant(
        depends=depends,
        dependency=depends.dependency,
        path=path,
        name=param_name,
    )


def get_sub_dependant(
    *,
    depends: params.Depends,
    dependency: Callable[..., Any],
    path: str,
    name: str | None = None,
) -> Dependant:
    sub_dependant = get_dependant(
        path=path,
        call=dependency,
        name=name,
        use_cache=depends.use_cache,
    )
    return sub_dependant


def get_dependant(
    *,
    path: str,
    call: Callable[..., Any],
    name: str | None = None,
    use_cache: bool = True,
) -> Dependant:
    endpoint_signature = get_typed_signature(call)
    signature_params = endpoint_signature.parameters
    dependant = Dependant(
        call=call,
        name=name,
        path=path,
        use_cache=use_cache,
    )
    for param_name, param in signature_params.items():
        if not is_annotated(param.annotation):
            warnings.warn(
                f"Parameter {param_name} is not annotated. Skipping parsing.",
                stacklevel=2,
            )
            continue

        param_details = analyze_param(
            param_name=param_name,
            annotation=param.annotation,
            value=param.default,
        )
        if param_details.depends is not None:
            sub_dependant = get_param_sub_dependant(
                param_name=param_name,
                depends=param_details.depends,
                path=path,
            )
            dependant.dependencies.append(sub_dependant)
            continue
        assert param_details.field is not None

        if isinstance(param_details.field.field_info, params.Path):
            assert param_details.field.field_info.is_required(), "Path parameters cannot have defaults"
            assert "{" + param_details.field.alias + "}" in path, (
                f"Path parameter {param_details.field.alias} not found in path {path}"
            )
            dependant.path_params.append(param_details.field)
        elif isinstance(param_details.field.field_info, params.Query):
            dependant.query_params.append(param_details.field)
        elif isinstance(param_details.field.field_info, params.Body):
            dependant.body_params.append(param_details.field)
        elif isinstance(param_details.field.field_info, params.Header):
            dependant.header_params.append(param_details.field)
        elif isinstance(param_details.field.field_info, params.Cookie):
            dependant.cookie_params.append(param_details.field)
        elif isinstance(param_details.field.field_info, params.Event):
            assert param_details.field.field_info.is_required(), "Event parameters cannot have defaults"
            dependant.event_params.append(param_details.field)
        elif isinstance(param_details.field.field_info, params.Context):
            assert param_details.field.field_info.is_required(), "Context parameters cannot have defaults"
            dependant.context_params.append(param_details.field)
        else:
            assert False, f"Unsupported dependency type: {param_details.field.field_info}"  # pragma: no cover

    return dependant


CacheKey = tuple[Callable[..., Any] | None, tuple[str, ...]]


def get_flat_dependant(
    dependant: Dependant,
    *,
    visited: list[CacheKey] = None,
) -> Dependant:
    if visited is None:
        visited = []
    cache_key = (dependant.call,)
    if cache_key in visited:
        return dependant
    visited.append(dependant.cache_key)

    flat_dependant = Dependant(
        path_params=dependant.path_params.copy(),
        query_params=dependant.query_params.copy(),
        body_params=dependant.body_params.copy(),
        header_params=dependant.header_params.copy(),
        cookie_params=dependant.cookie_params.copy(),
        event_params=dependant.event_params.copy(),
        context_params=dependant.context_params.copy(),
        use_cache=dependant.use_cache,
        path=dependant.path,
    )
    for sub_dependant in dependant.dependencies:
        if sub_dependant.cache_key in visited:
            continue
        flat_sub = get_flat_dependant(sub_dependant, visited=visited)
        flat_dependant.path_params.extend(flat_sub.path_params)
        flat_dependant.query_params.extend(flat_sub.query_params)
        flat_dependant.body_params.extend(flat_sub.body_params)
        flat_dependant.header_params.extend(flat_sub.header_params)
        flat_dependant.cookie_params.extend(flat_sub.cookie_params)
        flat_dependant.event_params.extend(flat_sub.event_params)
        flat_dependant.context_params.extend(flat_sub.context_params)

    return flat_dependant
