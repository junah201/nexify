from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from nexify.models import ModelField


@dataclass
class Dependant:
    path_params: list[ModelField] = field(default_factory=list)
    query_params: list[ModelField] = field(default_factory=list)
    body_params: list[ModelField] = field(default_factory=list)
    header_params: list[ModelField] = field(default_factory=list)
    cookie_params: list[ModelField] = field(default_factory=list)
    event_params: list[ModelField] = field(default_factory=list)
    context_params: list[ModelField] = field(default_factory=list)
    dependencies: list["Dependant"] = field(default_factory=list)
    name: str | None = None
    call: Callable[..., Any] | None = None
    use_cache: bool = True
    path: str | None = None
    cache_key: tuple[Callable[..., Any] | None, tuple[str, ...]] = field(init=False)

    def __post_init__(self) -> None:
        self.cache_key = (self.call,)
