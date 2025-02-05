from typing import Annotated

from nexify import Body, Nexify
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = Nexify()


@app.post("/items")
def create_item(item: Annotated[Item, Body()]):
    return item
