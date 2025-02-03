import json
from typing import Annotated

import pytest
from nexify import Nexify, Path


def test_no_path():
    app = Nexify()

    with pytest.raises(AssertionError):

        @app.get("/no_path")
        def no_path(foo: Annotated[int, Path()]): ...

    @app.get("/no_path/{id}")
    def no_path(id: Annotated[int, Path()]): ...

    res = no_path({"pathParameters": {}}, {})
    assert res == {
        "statusCode": 422,
        "headers": {"content-type": "application/json; charset=utf-8"},
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


def test_duplicated_path():
    app = Nexify()

    with pytest.raises(ValueError):

        @app.get("/duplicated_path/{foo}/{foo}")
        def duplicated_path(foo: Annotated[int, Path()]): ...
