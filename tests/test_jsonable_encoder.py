import datetime
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any

import pytest
from nexify.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

Undefined: Any = PydanticUndefined


@dataclass
class Foo:
    bar: str


class Bar(BaseModel):
    foo: str


class TestEnum(Enum):
    foo = "foo"
    bar = "bar"


@pytest.mark.parametrize(
    "obj,expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}),
        ({"foo": None}, {"foo": None}),
        ({"foo": datetime.datetime(2024, 2, 1)}, {"foo": "2024-02-01T00:00:00"}),
        ({"foo": Foo("123")}, {"foo": {"bar": "123"}}),
        ({1: {2: Decimal("3.14")}}, {1: {2: 3.14}}),
        ({"foo": Bar(foo="123")}, {"foo": {"foo": "123"}}),
        ({"foo": Undefined}, {"foo": None}),
        ({"foo": PurePath("foo")}, {"foo": "foo"}),
        ({"foo": TestEnum.foo}, {"foo": "foo"}),
        (
            [
                [1, 2, 3],
                Decimal(23.2),
                datetime.datetime(2024, 2, 1),
                Foo("123"),
                Bar(foo="123"),
                Undefined,
                PurePath("foo"),
                TestEnum.foo,
            ],
            [
                [1, 2, 3],
                23.2,
                "2024-02-01T00:00:00",
                {"bar": "123"},
                {"foo": "123"},
                None,
                "foo",
                "foo",
            ],
        ),
    ],
)
def test_jsonable_encoder(obj, expected):
    assert jsonable_encoder(obj) == expected


@pytest.mark.parametrize(
    "obj,expected",
    [
        (Foo("123"), {"bar": "123"}),
        (Bar(foo="123"), {"foo": "123"}),
    ],
)
def test_jsonable_encoder_with_single_pydantic_model(obj, expected):
    assert jsonable_encoder(obj) == expected
