from typing import Annotated

import pytest
from nexify import Nexify, Path
from nexify.exceptions import RequestValidationError


@pytest.mark.parametrize(
    "input",
    [
        ("bar"),
        (-23),
        (1.0),
        (None),
    ],
)
def test_invalid_path_with_gt(input):
    app = Nexify()

    @app.get("/path_with_invalid_input/{foo}")
    def path_with_invalid_input(foo: Annotated[int, Path(gt=10)]): ...

    with pytest.raises(RequestValidationError):
        path_with_invalid_input({"pathParameters": {"foo": input}}, {})


@pytest.mark.parametrize(
    "input",
    [
        ("1234"),
        ("fdsfsda"),
        (1.0),
        (None),
    ],
)
def test_invalid_path_with_max_length(input):
    app = Nexify()

    @app.get("/path_with_invalid_input/{foo}")
    def path_with_invalid_input(foo: Annotated[str, Path(max_length=3)]): ...

    with pytest.raises(RequestValidationError):
        path_with_invalid_input({"pathParameters": {"foo": input}}, {})


@pytest.mark.parametrize(
    "input",
    [
        ("1234"),
        ("fdsfsda"),
        (1.0),
        (None),
    ],
)
def test_invalid_path_with_min_length(input):
    app = Nexify()

    @app.get("/path_with_invalid_input/{foo}")
    def path_with_invalid_input(foo: Annotated[str, Path(min_length=10)]): ...

    with pytest.raises(RequestValidationError):
        path_with_invalid_input({"pathParameters": {"foo": input}}, {})


def test_no_path():
    app = Nexify()

    with pytest.raises(AssertionError):

        @app.get("/no_path")
        def no_path(foo: Annotated[int, Path()]): ...

    @app.get("/no_path/{id}")
    def no_path(id: Annotated[int, Path()]): ...

    with pytest.raises(RequestValidationError):
        no_path({}, {})


def test_duplicated_path():
    app = Nexify()

    with pytest.raises(ValueError):

        @app.get("/duplicated_path/{foo}/{foo}")
        def duplicated_path(foo: Annotated[int, Path()]): ...
