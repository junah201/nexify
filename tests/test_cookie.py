from decimal import Decimal
from typing import Annotated

import pytest
from nexify import Cookie, status


@pytest.mark.parametrize(
    "input,status_code,expected",
    [
        ("bar", status.HTTP_200_OK, "bar"),
        ("baz", status.HTTP_200_OK, "baz"),
        (None, status.HTTP_422_UNPROCESSABLE_ENTITY, None),
        ("BAR", status.HTTP_200_OK, "BAR"),
    ],
)
def test_cookie(app, input, status_code, expected):
    @app.get("/items")
    def read_items(foo: Annotated[str, Cookie()]):
        assert foo == expected

    cookies = {"foo": input} if input is not None else {}
    res = read_items({"cookies": cookies}, {})
    assert res["statusCode"] == status_code


@pytest.mark.parametrize(
    "input,status_code,validation",
    [
        ("11", status.HTTP_200_OK, {"gt": 10}),
        ("10", status.HTTP_422_UNPROCESSABLE_ENTITY, {"gt": 10}),
        ("10", status.HTTP_200_OK, {"ge": 10}),
        ("9", status.HTTP_422_UNPROCESSABLE_ENTITY, {"ge": 10}),
        ("9", status.HTTP_200_OK, {"lt": 10}),
        ("10", status.HTTP_422_UNPROCESSABLE_ENTITY, {"lt": 10}),
        ("10", status.HTTP_200_OK, {"le": 10}),
        ("11", status.HTTP_422_UNPROCESSABLE_ENTITY, {"le": 10}),
        ("10", status.HTTP_200_OK, {"multiple_of": 5}),
        ("7", status.HTTP_422_UNPROCESSABLE_ENTITY, {"multiple_of": 5}),
    ],
)
def test_cookie_with_validation_int(app, input, status_code, validation):
    @app.get("/items")
    def read_items(foo: Annotated[int, Cookie(**validation)]): ...

    res = read_items(
        {
            "cookies": {
                "foo": input,
            }
        },
        {},
    )
    assert res["statusCode"] == status_code


@pytest.mark.parametrize(
    "input,status_code,validation",
    [
        ("abc", status.HTTP_422_UNPROCESSABLE_ENTITY, {"min_length": 5}),
        ("abcdef", status.HTTP_200_OK, {"min_length": 5}),
        ("abcdef", status.HTTP_422_UNPROCESSABLE_ENTITY, {"max_length": 3}),
        ("abc", status.HTTP_200_OK, {"max_length": 3}),
        ("123", status.HTTP_200_OK, {"pattern": r"^\d{3}$"}),
        ("12a", status.HTTP_422_UNPROCESSABLE_ENTITY, {"pattern": r"^\d{3}$"}),
        ("abc", status.HTTP_200_OK, {"pattern": r"^[a-zA-Z]+$"}),
        ("123", status.HTTP_422_UNPROCESSABLE_ENTITY, {"pattern": r"^[a-zA-Z]+$"}),
    ],
)
def test_cookie_with_validation_str(app, input, status_code, validation):
    @app.get("/items")
    def read_items(foo: Annotated[str, Cookie(**validation)]): ...

    res = read_items(
        {
            "cookies": {
                "foo": input,
            }
        },
        {},
    )
    assert res["statusCode"] == status_code


@pytest.mark.parametrize(
    "input,status_code,validation",
    [
        ("11.5", status.HTTP_200_OK, {"gt": 10}),
        ("10.0", status.HTTP_422_UNPROCESSABLE_ENTITY, {"gt": 10}),
        ("10.0", status.HTTP_200_OK, {"ge": 10}),
        ("9.9", status.HTTP_422_UNPROCESSABLE_ENTITY, {"ge": 10}),
        ("9.9", status.HTTP_200_OK, {"lt": 10}),
        ("10.0", status.HTTP_422_UNPROCESSABLE_ENTITY, {"lt": 10}),
        ("10.0", status.HTTP_200_OK, {"le": 10}),
        ("10.1", status.HTTP_422_UNPROCESSABLE_ENTITY, {"le": 10}),
        ("inf", status.HTTP_422_UNPROCESSABLE_ENTITY, {"allow_inf_nan": False}),
        ("nan", status.HTTP_422_UNPROCESSABLE_ENTITY, {"allow_inf_nan": False}),
        ("1.23", status.HTTP_200_OK, {"allow_inf_nan": False}),
        ("10.0", status.HTTP_200_OK, {"multiple_of": 2.5}),
        ("7.1", status.HTTP_422_UNPROCESSABLE_ENTITY, {"multiple_of": 2.5}),
    ],
)
def test_cookie_with_validation_float(app, input, status_code, validation):
    @app.get("/items")
    def read_items(foo: Annotated[float, Cookie(**validation)]): ...

    res = read_items(
        {
            "cookies": {
                "foo": input,
            }
        },
        {},
    )
    assert res["statusCode"] == status_code


@pytest.mark.parametrize(
    "input,status_code,validation",
    [
        ("11.5", status.HTTP_200_OK, {"gt": 10}),
        ("10.0", status.HTTP_422_UNPROCESSABLE_ENTITY, {"gt": 10}),
        ("10.0", status.HTTP_200_OK, {"ge": 10}),
        ("9.9", status.HTTP_422_UNPROCESSABLE_ENTITY, {"ge": 10}),
        ("9.9", status.HTTP_200_OK, {"lt": 10}),
        ("10.0", status.HTTP_422_UNPROCESSABLE_ENTITY, {"lt": 10}),
        ("10.0", status.HTTP_200_OK, {"le": 10}),
        ("10.1", status.HTTP_422_UNPROCESSABLE_ENTITY, {"le": 10}),
        ("inf", status.HTTP_422_UNPROCESSABLE_ENTITY, {"allow_inf_nan": False}),
        ("nan", status.HTTP_422_UNPROCESSABLE_ENTITY, {"allow_inf_nan": False}),
        ("1.23", status.HTTP_200_OK, {"allow_inf_nan": False}),
        ("10.0", status.HTTP_200_OK, {"multiple_of": 2.5}),
        ("7.1", status.HTTP_422_UNPROCESSABLE_ENTITY, {"multiple_of": 2.5}),
        ("123.45", status.HTTP_200_OK, {"max_digits": 5, "decimal_places": 2}),
        ("12345.67", status.HTTP_422_UNPROCESSABLE_ENTITY, {"max_digits": 5, "decimal_places": 2}),
        ("123.456", status.HTTP_422_UNPROCESSABLE_ENTITY, {"max_digits": 5, "decimal_places": 2}),
    ],
)
def test_cookie_with_validation_decimal(app, input, status_code, validation):
    @app.get("/items")
    def read_items(foo: Annotated[Decimal, Cookie(**validation)]): ...

    res = read_items(
        {
            "cookies": {
                "foo": input,
            }
        },
        {},
    )
    assert res["statusCode"] == status_code
