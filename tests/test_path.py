from typing import Annotated
from uuid import UUID

import pytest
from nexify import Path, status


@pytest.mark.parametrize(
    "input,status_code,expected",
    [
        ("bar", status.HTTP_200_OK, "bar"),
        ("baz", status.HTTP_200_OK, "baz"),
        (None, status.HTTP_422_UNPROCESSABLE_ENTITY, None),
        ("BAR", status.HTTP_200_OK, "BAR"),
    ],
)
def test_path(app, input, status_code, expected):
    @app.get("/items/{item_id}")
    def read_item(item_id: Annotated[str, Path()]):
        assert item_id == expected

    res = read_item({"pathParameters": {"item_id": input}}, {})
    assert res["statusCode"] == status_code


@pytest.mark.parametrize(
    "input,status_code,validation",
    [
        (11, status.HTTP_200_OK, {"gt": 10}),
        (10, status.HTTP_422_UNPROCESSABLE_ENTITY, {"gt": 10}),
        (10, status.HTTP_200_OK, {"ge": 10}),
        (9, status.HTTP_422_UNPROCESSABLE_ENTITY, {"ge": 10}),
        (9, status.HTTP_200_OK, {"lt": 10}),
        (10, status.HTTP_422_UNPROCESSABLE_ENTITY, {"lt": 10}),
        (10, status.HTTP_200_OK, {"le": 10}),
        (11, status.HTTP_422_UNPROCESSABLE_ENTITY, {"le": 10}),
        (10, status.HTTP_200_OK, {"multiple_of": 5}),
        (7, status.HTTP_422_UNPROCESSABLE_ENTITY, {"multiple_of": 5}),
    ],
)
def test_path_with_validation_int(app, input, status_code, validation):
    @app.get("/items/{item_id}")
    def read_item(item_id: Annotated[int, Path(**validation)]): ...

    res = read_item({"pathParameters": {"item_id": str(input)}}, {})
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
    ],
)
def test_path_with_validation_str(app, input, status_code, validation):
    @app.get("/items/{item_id}")
    def read_item(item_id: Annotated[str, Path(**validation)]): ...

    res = read_item({"pathParameters": {"item_id": str(input)}}, {})
    assert res["statusCode"] == status_code


@pytest.mark.parametrize(
    "input,status_code",
    [
        ("550e8400-e29b-41d4-a716-446655440000", status.HTTP_200_OK),
        ("123e4567-e89b-12d3-a456-426614174000", status.HTTP_200_OK),
        ("invalid-uuid", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
def test_path_with_validation_uuid(app, input, status_code):
    @app.get("/items/{item_id}")
    def read_item(item_id: Annotated[UUID, Path()]):
        assert isinstance(item_id, UUID)

    res = read_item({"pathParameters": {"item_id": str(input)}}, {})
    assert res["statusCode"] == status_code
