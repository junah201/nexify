from typing import Annotated

from nexify import Nexify, Path

app = Nexify()


@app.get("/items/{item_id}")
def read_item(
    item_id: Annotated[
        str,
        Path(
            openapi_examples={
                "Test item: Foo": {
                    "summary": "Item ID of a test item (Foo)",
                    "value": "2341",
                },
                "Test item: Bar": {
                    "summary": "Item ID of a test item (Bar)",
                    "value": "2342",
                },
            }
        ),
    ],
) -> dict:
    return {"item_id": item_id}
