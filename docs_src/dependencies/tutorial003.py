from typing import Annotated

from nexify import Depends, Nexify, Query

app = Nexify()


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
def read_items(commons: Annotated[CommonQueryParams, Depends(CommonQueryParams)]):
    return commons
