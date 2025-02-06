from typing import Annotated

from nexify import Body, Nexify
from pydantic import BaseModel, Field

app = Nexify()


class Item(BaseModel):
    name: str
    description: Annotated[
        str | None,
        Field(
            default=None,
            description="The description of the item",
            max_length=300,
        ),
    ]
    price: Annotated[
        float,
        Field(
            gt=0,
            description="The price must be greater than zero",
        ),
    ]
    tax: Annotated[
        float | None,
        Field(
            default=None,
            gt=0,
        ),
    ]


@app.post("/items")
def create_item(item: Annotated[Item, Body()]):
    return item.model_dump()
