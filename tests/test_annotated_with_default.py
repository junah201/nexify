import json
from typing import Annotated

import pytest
from nexify import Body, Context, Event, Nexify, Path, Query
from nexify.exceptions import RequestValidationError
from pydantic import BaseModel


@pytest.mark.parametrize(
    "default",
    [
        ("bar"),
        ("baz"),
        ("qux"),
    ],
)
def test_query_with_default(default):
    app = Nexify()

    @app.get("/query_with_default")
    def query_with_default(foo: Annotated[str, Query()] = default):
        assert foo == default

    @app.get("/query_with_query_default")
    def query_with_query_default(foo: Annotated[str, Query(default=default)]):
        assert foo == default

    @app.get("/query_with_query_default_factory")
    def query_with_query_default_factory(foo: Annotated[str, Query(default_factory=lambda: default)]):
        assert foo == default

    query_with_default({}, {})
    query_with_query_default({}, {})
    query_with_query_default_factory({}, {})


def test_query_with_no_default():
    app = Nexify()

    @app.get("/query_with_no_default")
    def query_with_no_default(foo: Annotated[str, Query()]): ...

    with pytest.raises(RequestValidationError):
        query_with_no_default({}, {})


@pytest.mark.parametrize(
    "default",
    [
        ("bar"),
        ("baz"),
        ("qux"),
    ],
)
def test_path_with_default(
    default,
):
    app = Nexify()

    with pytest.raises(AssertionError):

        @app.get("/path_with_default")
        def path_with_default(foo: Annotated[str, Path()] = default): ...

    with pytest.raises(AssertionError):

        @app.get("/path_with_path_default")
        def path_with_path_default(foo: Annotated[str, Path(default=default)]): ...

    with pytest.raises(AssertionError):

        @app.get("/path_with_path_default_factory")
        def path_with_path_default_factory(foo: Annotated[str, Path(default_factory=lambda: default)]): ...


def test_path_with_no_default():
    app = Nexify()

    with pytest.raises(AssertionError):

        @app.get("/path_with_no_default")
        def path_with_no_default(foo: Annotated[str, Path()]): ...

    @app.get("/path_with_no_default/{foo}")
    def path_with_no_default(foo: Annotated[str, Path()]): ...


def test_body_with_default():
    app = Nexify()

    @app.get("/body_with_default")
    def body_with_default(foo: Annotated[dict, Body()] = {"foo": "bar"}):
        assert foo == {"foo": "bar"}

    @app.get("/body_with_body_default")
    def body_with_body_default(foo: Annotated[dict, Body(default={"foo": "bar"})]):
        assert foo == {"foo": "bar"}

    @app.get("/body_with_body_default_factory")
    def body_with_body_default_factory(foo: Annotated[dict, Body(default_factory=lambda: {"foo": "bar"})]):
        assert foo == {"foo": "bar"}

    body_with_default({}, {})
    body_with_body_default({}, {})
    body_with_body_default_factory({}, {})


def test_body_with_no_default():
    app = Nexify()

    class Foo(BaseModel):
        foo: str

    @app.get("/body_with_no_default")
    def body_with_no_default_dict(foo: Annotated[dict, Body()]):
        assert json.dumps(foo, sort_keys=True) == json.dumps({"foo": "bar"}, sort_keys=True)

    @app.get("/body_with_no_default")
    def body_with_no_default_pydantic(foo: Annotated[Foo, Body()]):
        assert foo == Foo(foo="bar")

    with pytest.raises(RequestValidationError):
        body_with_no_default_dict({}, {})

    with pytest.raises(RequestValidationError):
        body_with_no_default_pydantic({}, {})

    event = {
        "body": json.dumps({"foo": "bar"}),
    }

    body_with_no_default_dict(event, {})
    body_with_no_default_pydantic(event, {})


def test_event_with_default():
    app = Nexify()

    with pytest.raises(AssertionError):

        @app.get("/event_with_default")
        def event_with_default(foo: Annotated[dict, Event()] = {"foo": "bar"}): ...


def test_event_with_no_default():
    app = Nexify()

    @app.get("/event_with_no_default")
    def event_with_no_default(event: Annotated[dict, Event()]):
        assert event == {"foo": "bar"}

    event_with_no_default({"foo": "bar"}, {})


def test_context_with_default():
    app = Nexify()

    with pytest.raises(AssertionError):

        @app.get("/context_with_default")
        def context_with_default(context: Annotated[dict, Context()] = {"foo": "bar"}): ...


def test_context_with_no_default():
    app = Nexify()

    @app.get("/context_with_no_default")
    def context_with_no_default(context: Annotated[dict, Context()]):
        assert context == {"foo": "bar"}

    context_with_no_default({}, {"foo": "bar"})
