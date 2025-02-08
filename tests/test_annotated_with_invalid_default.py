from typing import Annotated

import pytest
from nexify import Body, Query
from pydantic import BaseModel


def test_query_with_multiple_default(app):
    with pytest.raises((AssertionError, TypeError)):

        @app.get("/query_with_multiple_default")
        def query_with_multiple_default(
            foo: Annotated[
                str,
                Query(
                    default="bar",
                    default_factory=lambda: "baz",
                ),
            ],
        ): ...

    with pytest.raises((AssertionError, TypeError)):

        @app.get("/query_with_multiple_default")
        def query_with_multiple_default(
            foo: Annotated[
                str,
                Query(
                    default_factory=lambda: "baz",
                ),
            ] = "bar",
        ): ...

    with pytest.raises((AssertionError, TypeError)):

        @app.get("/query_with_multiple_default")
        def query_with_multiple_default(
            foo: Annotated[
                str,
                Query(
                    default="bar",
                ),
            ] = "baz",
        ): ...


def test_body_with_multiple_default(app):
    class SampleModel(BaseModel):
        name: str

    with pytest.raises((AssertionError, TypeError)):

        @app.get("/body_with_multiple_default")
        def body_with_multiple_default(
            data: Annotated[
                SampleModel,
                Body(
                    default=SampleModel(name="foo"),
                    default_factory=lambda: SampleModel(name="bar"),
                ),
            ],
        ): ...

    with pytest.raises((AssertionError, TypeError)):

        @app.get("/body_with_multiple_default")
        def body_with_multiple_default(
            data: Annotated[
                SampleModel,
                Body(
                    default_factory=lambda: SampleModel(name="bar"),
                ),
            ] = SampleModel(name="foo"),
        ): ...

    with pytest.raises((AssertionError, TypeError)):

        @app.get("/body_with_multiple_default")
        def body_with_multiple_default(
            data: Annotated[
                SampleModel,
                Body(
                    default=SampleModel(name="foo"),
                ),
            ] = SampleModel(name="bar"),
        ): ...
