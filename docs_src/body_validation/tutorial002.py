from typing import Annotated

from nexify import Body, Nexify
from pydantic import BaseModel

app = Nexify()


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@app.post("/items")
def create_item(
    item: Annotated[
        Item,
        Body(
            openapi_examples={
                "simple_example": {
                    "summary": "Simple Example",
                    "description": "A simple example of a request to create an item",
                    "value": {
                        "name": "Item Name",
                        "description": "Item Description",
                        "price": 10.5,
                        "tax": 1.5,
                    },
                }
            },
        ),
    ],
):
    return item.model_dump()
