from typing import Annotated

from nexify import Nexify, Path

app = Nexify()


@app.get("/items/{item_id}/users/{user_id}")
def read_item(item_id: Annotated[int, Path()], user_id: Annotated[str, Path()]):
    return {"item_id": item_id, "user_id": user_id}
