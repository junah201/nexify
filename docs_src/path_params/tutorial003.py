from typing import Annotated

from nexify import Nexify, Path

app = Nexify()


@app.get("/items/all")
def read_all_items():
    return {"items": "all"}


@app.get("/items/{item_id}")
def read_item(item_id: Annotated[int, Path()]):
    return {"item_id": item_id}
