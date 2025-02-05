from typing import Annotated

from nexify import Nexify, Path, Query

app = Nexify()


@app.get("/items/{item_id}")
def read_item(
    item_id: Annotated[str | None, Path()] = None,
    itemId: Annotated[
        str | None,
        Query(deprecated=True, description="This parameter is deprecated"),
    ] = None,
) -> dict:
    if itemId:
        return {"item_id": itemId}
    return {"item_id": item_id}
