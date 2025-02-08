from typing import Annotated

import pytest
from nexify import Context, Event, Path, Query


@pytest.mark.parametrize(
    "event,expected",
    [
        ({"queryStringParameters": {"foo": "bar"}}, "bar"),
        ({"queryStringParameters": {"foo": "baz"}}, "baz"),
        ({"queryStringParameters": {"foo": "qux"}}, "qux"),
    ],
)
def test_query(app, event, expected):
    @app.get("/query")
    def query(foo: Annotated[str, Query()]):
        assert foo == expected

    query(event, {})


@pytest.mark.parametrize(
    "event,expected",
    [
        ({"pathParameters": {"foo": "bar"}}, "bar"),
        ({"pathParameters": {"foo": "baz"}}, "baz"),
        ({"pathParameters": {"foo": "qux"}}, "qux"),
    ],
)
def test_path(app, event, expected):
    @app.get("/path/{foo}")
    def path(foo: Annotated[str, Path()]):
        assert foo == expected

    path(event, {})


@pytest.mark.parametrize(
    "given_event",
    [
        ({"foo": "bar"}),
        ({"foo": "baz"}),
        ({"foo": "qux"}),
    ],
)
def test_event(app, given_event):
    @app.get("/event")
    def event(foo: Annotated[dict, Event()]):
        assert foo == given_event

    event(given_event, {})


@pytest.mark.parametrize(
    "given_context",
    [
        ({"foo": "bar"}),
        ({"foo": "baz"}),
        ({"foo": "qux"}),
    ],
)
def test_context(app, given_context):
    @app.get("/context")
    def context(foo: Annotated[dict, Context()]):
        assert foo == given_context

    context({}, given_context)


def test_no_annotated_parameter(app):
    with pytest.warns(UserWarning, match=r"Parameter .* is not annotated\. Skipping parsing\."):

        @app.get("/no-annotated-parameter")
        def no_annotated_parameter(foo):
            assert foo == "bar"
