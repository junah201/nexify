import json
from typing import Annotated

import pytest
from nexify import Path


@pytest.mark.parametrize(
    "input",
    [
        ("-23"),
        ("0"),
    ],
)
def test_invalid_path_with_gt(app, input):
    @app.get("/path_with_invalid_input/{foo}")
    def path_with_invalid_input(foo: Annotated[int, Path(gt=10)]): ...

    res = path_with_invalid_input({"pathParameters": {"foo": input}}, {})
    assert res == {
        "statusCode": 422,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(
            {
                "detail": [
                    {
                        "type": "greater_than",
                        "loc": ["path", "foo"],
                        "msg": "Input should be greater than 10",
                        "input": input,
                        "ctx": {"gt": 10},
                    }
                ]
            }
        ),
    }


@pytest.mark.parametrize(
    "input",
    [
        ("1234"),
        ("fdsfsda"),
    ],
)
def test_invalid_path_with_max_length(app, input):
    @app.get("/path_with_invalid_input/{foo}")
    def path_with_invalid_input(foo: Annotated[str, Path(max_length=3)]): ...

    res = path_with_invalid_input({"pathParameters": {"foo": input}}, {})
    assert res == {
        "statusCode": 422,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(
            {
                "detail": [
                    {
                        "type": "string_too_long",
                        "loc": ["path", "foo"],
                        "msg": "String should have at most 3 characters",
                        "input": input,
                        "ctx": {"max_length": 3},
                    }
                ]
            }
        ),
    }


@pytest.mark.parametrize(
    "input",
    [("1234"), ("fdsfsda")],
)
def test_invalid_path_with_min_length(app, input):
    @app.get("/path_with_invalid_input/{foo}")
    def path_with_invalid_input(foo: Annotated[str, Path(min_length=10)]): ...

    res = path_with_invalid_input({"pathParameters": {"foo": input}}, {})
    assert res == {
        "statusCode": 422,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["path", "foo"],
                        "msg": "String should have at least 10 characters",
                        "input": input,
                        "ctx": {"min_length": 10},
                    }
                ]
            }
        ),
    }


def test_no_path(app):
    with pytest.raises(AssertionError):

        @app.get("/no_path")
        def no_path(foo: Annotated[int, Path()]): ...

    @app.get("/no_path/{id}")
    def no_path(id: Annotated[int, Path()]): ...

    response = no_path({}, {})
    assert response == {
        "statusCode": 422,
        "headers": {
            "content-type": "application/json; charset=utf-8",
        },
        "body": json.dumps(
            {
                "detail": [
                    {
                        "type": "int_type",
                        "loc": ["path", "id"],
                        "msg": "Input should be a valid integer",
                        "input": None,
                    }
                ]
            }
        ),
    }


def test_duplicated_path(app):
    with pytest.raises(ValueError):

        @app.get("/duplicated_path/{foo}/{foo}")
        def duplicated_path(foo: Annotated[int, Path()]): ...


@pytest.mark.parametrize(
    "input",
    [
        ("not_an_int"),
        ("fdsfsda"),
    ],
)
def test_invalid_path(app, input):
    @app.get("/items/{item_id}")
    def read_item(item_id: Annotated[int, Path()]): ...

    assert read_item({"pathParameters": {"item_id": input}}, {}) == {
        "statusCode": 422,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps(
            {
                "detail": [
                    {
                        "type": "int_parsing",
                        "loc": ["path", "item_id"],
                        "msg": "Input should be a valid integer, unable to parse string as an integer",
                        "input": input,
                    }
                ]
            }
        ),
    }
