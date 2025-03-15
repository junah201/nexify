from typing import Annotated

from nexify import Depends, Nexify, Query

app = Nexify()


def common_parameters(
    q: Annotated[str | None, Query()] = None,
    skip: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items")
def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons


@app.get("/users")
def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
