from typing import Annotated

from nexify import Nexify, Path

app = Nexify()


@app.get("/items/{item_id}")
def read_item(
    item_id: Annotated[
        str,
        Path(
            title="Item ID",
            description="This is Item ID",
        ),
    ],
) -> dict:
    return {"item_id": item_id}
