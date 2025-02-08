from typing import Annotated

import pytest
from nexify import Depends, Nexify, Query
from nexify.encoders import jsonable_encoder


def test_depends(app):
    def common_parameters(
        q: Annotated[str | None, Query()] = None,
        skip: Annotated[int, Query()] = 0,
        limit: Annotated[int, Query()] = 100,
    ):
        return {"q": q, "skip": skip, "limit": limit}

    @app.get("/items")
    def read_items(
        common: Annotated[dict, Depends(common_parameters)],
    ):
        assert common == {"q": "foo", "skip": 5, "limit": 50}

    read_items(
        {
            "queryStringParameters": {
                "q": "foo",
                "skip": 5,
                "limit": 50,
            }
        },
        {},
    )


@pytest.mark.parametrize(
    "q,skip,limit",
    [
        ("foo", 5, 50),
        ("baz", 15, 150),
    ],
)
def test_depends_with_class(
    app,
    q,
    skip,
    limit,
):
    class CommonQueryParams:
        def __init__(
            self,
            q: Annotated[str | None, Query()] = None,
            skip: Annotated[int, Query()] = 0,
            limit: Annotated[int, Query()] = 100,
        ):
            self.q = q
            self.skip = skip
            self.limit = limit

    @app.get("/items")
    def read_items(
        common: Annotated[CommonQueryParams, Depends(CommonQueryParams)],
    ):
        assert jsonable_encoder(common) == jsonable_encoder(CommonQueryParams(q=q, skip=skip, limit=limit))

    read_items(
        {
            "queryStringParameters": {
                "q": q,
                "skip": skip,
                "limit": limit,
            }
        },
        {},
    )


def test_nested_depends(app):
    def common_parameters(
        skip: Annotated[int, Query()] = 0,
        limit: Annotated[int, Query()] = 100,
    ):
        return {"skip": skip, "limit": limit}

    def search_parameters(
        q: Annotated[str | None, Query(default=None)],
        common: Annotated[dict, Depends(common_parameters)],
    ):
        return {"q": q, **common}

    @app.get("/items")
    def read_items(
        search: Annotated[dict, Depends(search_parameters)],
    ):
        assert search == {"q": "foo", "skip": 5, "limit": 50}


@pytest.mark.parametrize(
    "token,expected_status",
    [
        (None, 500),
        ("invalid-token", 500),
        ("fake-super-secret-token", 200),
    ],
)
def test_depends_with_verify(app, token, expected_status):
    def verify_token(x_token: Annotated[str | None, Query(default=None)]):
        if x_token != "fake-super-secret-token":
            raise ValueError("Unauthorized", 401)

    @app.get("/items", dependencies=[Depends(verify_token)])
    def read_items():
        return {"items": [{"item": "Portal Gun"}, {"item": "Plumbus"}]}

    query_params = {"queryStringParameters": {"x_token": token}} if token else {}

    res = read_items(query_params, {})
    assert res["statusCode"] == expected_status


@pytest.mark.parametrize(
    "token,expected_status",
    [
        (None, 500),
        ("invalid-token", 500),
        ("fake-super-secret-token", 200),
    ],
)
def test_global_dependencies(token, expected_status):
    def verify_token(x_token: Annotated[str | None, Query(default=None)]):
        if x_token != "fake-super-secret-token":
            raise ValueError("Unauthorized", 401)

    app = Nexify(dependencies=[Depends(verify_token)])

    @app.get("/items")
    def read_items():
        return {"items": [{"item": "Portal Gun"}, {"item": "Plumbus"}]}

    query_params = {"queryStringParameters": {"x_token": token}} if token else {}

    res = read_items(query_params, {})
    assert res["statusCode"] == expected_status


@pytest.mark.parametrize(
    "input",
    [
        ("test_user"),
    ],
)
def test_depends_with_yield(app, input):
    flag = False

    def get_username():
        try:
            yield input
        finally:
            assert flag is True

    @app.get("/user")
    def read_user(username: Annotated[str, Depends(get_username)]):
        assert username == input
        nonlocal flag
        flag = True

    read_user({}, {})


@pytest.mark.parametrize(
    "input",
    [
        ("fdsfsda"),
    ],
)
def test_depends_with_invalid_input_in_sub_depends(app, input):
    def common_parameters(
        skip: Annotated[int, Query()] = 0,
        limit: Annotated[int, Query()] = 100,
    ):
        return {"skip": skip, "limit": limit}

    @app.get("/items")
    def read_items(
        common: Annotated[dict, Depends(common_parameters)],
    ): ...

    res = read_items(
        {
            "queryStringParameters": {
                "skip": input,
                "limit": 50,
            }
        },
        {},
    )
    assert res["statusCode"] == 422


@pytest.mark.parametrize(
    "input,status_code",
    [
        ("fdsfsda", 422),
        ("1234", 200),
    ],
)
def test_depends_with_invalid_input_in_sub_sub_depends(app, input, status_code):
    def common_parameters(
        skip: Annotated[int, Query()] = 0,
        limit: Annotated[int, Query()] = 100,
    ):
        return {"skip": skip, "limit": limit}

    def search_parameters(
        q: Annotated[str | None, Query(default=None)],
        common: Annotated[dict, Depends(common_parameters)],
    ):
        return {"q": q, **common}

    @app.get("/items")
    def read_items(
        search: Annotated[dict, Depends(search_parameters)],
    ): ...

    res = read_items(
        {
            "queryStringParameters": {
                "skip": input,
                "limit": 50,
            }
        },
        {},
    )
    assert res["statusCode"] == status_code
