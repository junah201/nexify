import inspect
from collections.abc import Sequence
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    Literal,
)

from nexify.types import IncEx
from pydantic import TypeAdapter, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

Undefined: Any = PydanticUndefined


@dataclass
class ModelField:
    field_info: FieldInfo
    name: str
    mode: Literal["validation", "serialization"] = "validation"

    @property
    def alias(self) -> str:
        a = self.field_info.alias
        return a if a is not None else self.name

    @property
    def required(self) -> bool:
        return self.field_info.is_required()

    @property
    def default(self) -> Any:
        if self.field_info.is_required():
            return Undefined
        return self.field_info.get_default(call_default_factory=True)

    @property
    def type_(self) -> Any:
        return self.field_info.annotation

    def __post_init__(self) -> None:
        self._type_adapter: TypeAdapter[Any] = TypeAdapter(Annotated[self.field_info.annotation, self.field_info])

    def validate(
        self,
        object: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool = True,
        context: dict[str, Any] | None = None,
        experimental_allow_partial: bool | Literal["off", "on", "trailing-strings"] = False,
        loc: tuple[str | int, ...] = (),
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        try:
            return (
                self._type_adapter.validate_python(
                    object,
                    strict=strict,
                    from_attributes=from_attributes,
                    context=context,
                    experimental_allow_partial=experimental_allow_partial,
                ),
                None,
            )
        except ValidationError as exc:
            return None, _regenerate_error_with_loc(errors=exc.errors(include_url=False), loc_prefix=loc)

    def serialize(
        self,
        instance: Any,
        /,
        *,
        mode: Literal["json", "python"] = "json",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        serialize_as_any: bool = False,
        context: dict[str, Any] | None = None,
    ) -> Any:
        # What calls this code passes a value that already called
        # self._type_adapter.validate_python(value)
        return self._type_adapter.dump_python(
            instance,
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
            context=context,
        )

    def __hash__(self) -> int:
        return id(self)


def create_model_field(
    field_info: FieldInfo,
    annotation: type[Any],
    name: str,
    default: Any = inspect.Parameter.empty,
) -> ModelField:
    field_info.annotation = annotation
    if default is not inspect.Parameter.empty:
        assert field_info.is_required(), "Cannot set default value for a field that already has a default value set"
        field_info.default = default
    if field_info.alias is None:
        field_info.alias = name
    return ModelField(
        field_info=field_info,
        name=name,
        mode="validation",
    )


def _regenerate_error_with_loc(*, errors: Sequence[Any], loc_prefix: tuple[str | int, ...]) -> list[dict[str, Any]]:
    updated_loc_errors: list[Any] = [{**err, "loc": loc_prefix + err.get("loc", ())} for err in errors]

    return updated_loc_errors
