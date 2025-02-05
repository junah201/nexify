from typing import Annotated

from nexify import Nexify, Path

app = Nexify()


@app.get("/items/{item_id}")
def read_item(item_id: Annotated[str, Path(min_length=2, max_length=8)]) -> dict:
    return {"item_id": item_id}
