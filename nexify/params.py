import json
from collections.abc import Callable
from enum import Enum
from typing import Any

from annotated_types import SupportsGe, SupportsGt, SupportsLe, SupportsLt
from nexify.openapi.models import Example
from pydantic import AliasChoices, AliasPath
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import deprecated

Undefined: Any = PydanticUndefined


class ParamTypes(Enum):
    query = "query"
    path = "path"
    header = "header"
    cookie = "cookie"


class Param(FieldInfo):
    in_: ParamTypes

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Callable[[], Any] | None = Undefined,
        annotation: Any | None = None,
        alias: str | None = None,
        alias_priority: int | None = Undefined,
        validation_alias: str | AliasPath | AliasChoices | None = None,
        serialization_alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: SupportsGt | None = None,
        ge: SupportsGe | None = None,
        lt: SupportsLt | None = None,
        le: SupportsLe | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        discriminator: str | None = None,
        strict: bool | None = Undefined,
        multiple_of: float | None = Undefined,
        allow_inf_nan: bool | None = Undefined,
        max_digits: int | None = Undefined,
        decimal_places: int | None = Undefined,
        examples: list[Any] | None = None,
        openapi_examples: dict[str, Example] | None = None,
        deprecated: deprecated | str | bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
    ):
        self.include_in_schema = include_in_schema
        self.openapi_examples = openapi_examples
        kwargs = {
            "default": default,
            "default_factory": default_factory,
            "annotation": annotation,
            "alias": alias,
            "alias_priority": alias_priority,
            "validation_alias": validation_alias,
            "serialization_alias": serialization_alias,
            "title": title,
            "description": description,
            "gt": gt,
            "ge": ge,
            "lt": lt,
            "le": le,
            "min_length": min_length,
            "max_length": max_length,
            "pattern": pattern,
            "discriminator": discriminator,
            "strict": strict,
            "multiple_of": multiple_of,
            "allow_inf_nan": allow_inf_nan,
            "max_digits": max_digits,
            "decimal_places": decimal_places,
            "examples": examples,
            "deprecated": deprecated,
            "json_schema_extra": json_schema_extra,
        }

        use_kwargs = {k: v for k, v in kwargs.items() if v is not Undefined}

        super().__init__(**use_kwargs)

    @classmethod
    def get_source(cls, event: dict, context: dict) -> Any:
        raise NotImplementedError  # pragma: no cover

    def get_value_from_source(self, source: dict, default_value: Any = Undefined) -> Any:
        raise NotImplementedError  # pragma: no cover

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):
    in_ = ParamTypes.path

    def __init__(
        self,
        default: Any = ...,
        *,
        default_factory: Callable[[], Any] | None = Undefined,
        annotation: Any | None = None,
        alias: str | None = None,
        alias_priority: int | None = Undefined,
        validation_alias: str | AliasPath | AliasChoices | None = None,
        serialization_alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: SupportsGt | None = None,
        ge: SupportsGe | None = None,
        lt: SupportsLt | None = None,
        le: SupportsLe | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        discriminator: str | None = None,
        strict: bool | None = Undefined,
        multiple_of: float | None = Undefined,
        allow_inf_nan: bool | None = Undefined,
        max_digits: int | None = Undefined,
        decimal_places: int | None = Undefined,
        examples: list[Any] | None = None,
        openapi_examples: dict[str, Example] | None = None,
        deprecated: deprecated | str | bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
    ):
        assert default is ..., "Path parameters cannot have a default value"
        assert default_factory is Undefined, "Path parameters cannot have a default factory"
        self.in_ = self.in_
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
        )

    @classmethod
    def get_source(cls, event: dict, context: dict) -> dict:
        return event.get("pathParameters", {}) or {}

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        default = self.get_default(call_default_factory=True)
        default = default if default is not Undefined else default_value

        value = source.get(self.alias, default)
        return value, None


class Query(Param):
    in_ = ParamTypes.query

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Callable[[], Any] | None = Undefined,
        annotation: Any | None = None,
        alias: str | None = None,
        alias_priority: int | None = Undefined,
        validation_alias: str | AliasPath | AliasChoices | None = None,
        serialization_alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: SupportsGt | None = None,
        ge: SupportsGe | None = None,
        lt: SupportsLt | None = None,
        le: SupportsLe | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        discriminator: str | None = None,
        strict: bool | None = Undefined,
        multiple_of: float | None = Undefined,
        allow_inf_nan: bool | None = Undefined,
        max_digits: int | None = Undefined,
        decimal_places: int | None = Undefined,
        examples: list[Any] | None = None,
        openapi_examples: dict[str, Example] | None = None,
        deprecated: deprecated | str | bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
        )

    @classmethod
    def get_source(cls, event: dict, context: dict) -> dict:
        return event.get("queryStringParameters", {}) or {}

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        default = self.get_default(call_default_factory=True)
        default = default if default is not Undefined else default_value

        value = source.get(self.alias, default)
        if value is Undefined:
            return None, [{"loc": ["query", self.alias], "msg": "Field required", "type": "missing", "input": None}]
        return value, None


class Header(Param):
    in_ = ParamTypes.header

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Callable[[], Any] | None = Undefined,
        annotation: Any | None = None,
        alias: str | None = None,
        alias_priority: int | None = Undefined,
        validation_alias: str | AliasPath | AliasChoices | None,
        serialization_alias: str | None = None,
        convert_underscores: bool = True,
        title: str | None = None,
        description: str | None = None,
        gt: SupportsGt | None = None,
        ge: SupportsGe | None = None,
        lt: SupportsLt | None = None,
        le: SupportsLe | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        discriminator: str | None = None,
        strict: bool | None = Undefined,
        multiple_of: float | None = Undefined,
        allow_inf_nan: bool | None = Undefined,
        max_digits: int | None = Undefined,
        decimal_places: int | None = Undefined,
        examples: list[Any] | None = None,
        openapi_examples: dict[str, Example] | None = None,
        deprecated: deprecated | str | bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
    ):
        self.convert_underscores = convert_underscores
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
        )

    @classmethod
    def get_source(cls, event: dict, context: dict) -> dict:
        return event.get("headers", {}) or {}

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        default = self.get_default(call_default_factory=True)
        default = default if default is not Undefined else default_value

        value = source.get(self.alias.lower().replace("_", "-"), default)
        if value is Undefined:
            return None, [{"loc": ["header", self.alias], "msg": "Field required", "type": "missing", "input": None}]
        return value, None


class Cookie(Param):
    in_ = ParamTypes.cookie

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Callable[[], Any] | None = Undefined,
        annotation: Any | None = None,
        alias: str | None = None,
        alias_priority: int | None = Undefined,
        validation_alias: str | AliasPath | AliasChoices | None,
        serialization_alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: SupportsGt | None = None,
        ge: SupportsGe | None = None,
        lt: SupportsLt | None = None,
        le: SupportsLe | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        discriminator: str | None = None,
        strict: bool | None = Undefined,
        multiple_of: float | None = Undefined,
        allow_inf_nan: bool | None = Undefined,
        max_digits: int | None = Undefined,
        decimal_places: int | None = Undefined,
        examples: list[Any] | None = None,
        openapi_examples: dict[str, Example] | None = None,
        deprecated: deprecated | str | bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
        )

    @classmethod
    def get_source(cls, event: dict, context: dict) -> dict:
        return event.get("cookies", {}) or {}

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        default = self.get_default(call_default_factory=True)
        default = default if default is not Undefined else default_value

        value = source.get(self.alias.replace("_", "-"), default)
        if value is Undefined:
            return None, [{"loc": ["cookie", self.alias], "msg": "Field required", "type": "missing", "input": None}]
        return value, None


class Body(FieldInfo):
    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Callable[[], Any] | None = Undefined,
        annotation: Any | None = None,
        embed: bool | None = None,
        media_type: str = "application/json",
        alias: str | None = None,
        alias_priority: int | None = Undefined,
        validation_alias: str | AliasPath | AliasChoices | None = None,
        serialization_alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: SupportsGt | None = None,
        ge: SupportsGe | None = None,
        lt: SupportsLt | None = None,
        le: SupportsLe | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        discriminator: str | None = None,
        strict: bool | None = Undefined,
        multiple_of: float | None = Undefined,
        allow_inf_nan: bool | None = Undefined,
        max_digits: int | None = Undefined,
        decimal_places: int | None = Undefined,
        examples: list[Any] | None = None,
        openapi_examples: dict[str, Example] | None = None,
        deprecated: deprecated | str | bool | None = None,
        include_in_schema: bool = True,
        json_schema_extra: dict[str, Any] | None = None,
    ):
        self.embed = embed
        self.media_type = media_type
        self.include_in_schema = include_in_schema
        self.openapi_examples = openapi_examples
        kwargs = {
            "default": default,
            "default_factory": default_factory,
            "annotation": annotation,
            "alias": alias,
            "alias_priority": alias_priority,
            "validation_alias": validation_alias,
            "serialization_alias": serialization_alias,
            "title": title,
            "description": description,
            "gt": gt,
            "ge": ge,
            "lt": lt,
            "le": le,
            "min_length": min_length,
            "max_length": max_length,
            "pattern": pattern,
            "discriminator": discriminator,
            "strict": strict,
            "multiple_of": multiple_of,
            "allow_inf_nan": allow_inf_nan,
            "max_digits": max_digits,
            "decimal_places": decimal_places,
            "examples": examples,
            "deprecated": deprecated,
            "json_schema_extra": json_schema_extra,
        }

        use_kwargs = {k: v for k, v in kwargs.items() if v is not Undefined}

        super().__init__(**use_kwargs)

    def get_source(self, event: dict, context: dict) -> dict:
        return json.loads(event.get("body", "{}")) or {}

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        default = self.get_default(call_default_factory=True)
        default = default if default is not Undefined else default_value
        value = source or default
        if value is Undefined:
            return None, [{"loc": ["body"], "msg": "Field required", "type": "missing", "input": None}]
        return value, None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Event(FieldInfo):
    @classmethod
    def get_source(cls, event: dict, context: dict) -> dict:
        return event

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        assert default_value is Undefined, "Event parameter must do not have default values"
        return source, None


class Context(FieldInfo):
    @classmethod
    def get_source(cls, event: dict, context: dict) -> dict:
        return context

    def get_value_from_source(
        self, source: dict, default_value: Any = Undefined
    ) -> tuple[Any, list[dict[str, Any]] | None]:
        assert default_value is Undefined, "Context parameter must do not have default values"
        return source, None


class Response(FieldInfo): ...


class Depends:
    def __init__(self, dependency: Callable[..., Any] | None = None, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"{self.__class__.__name__}({attr}{cache})"
