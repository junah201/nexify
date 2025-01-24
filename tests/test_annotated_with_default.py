from typing import Annotated

import pytest
from nexify import Nexify, Query


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

    with pytest.raises(TypeError):
        query_with_no_default({}, {})
