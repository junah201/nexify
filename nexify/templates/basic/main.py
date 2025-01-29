from typing import Annotated

from nexify import Body, Nexify, Path, Query, status
from pydantic import BaseModel, Field

app = Nexify(title="My Nexify API", version="0.1.0")


class Item(BaseModel):
    id: str
    name: str
    price: Annotated[int, Field(ge=0)]


@app.get("/items")
def read_items(limit: Annotated[int, Query(default=10)]) -> list[Item]:
    return [Item(id=f"{i + 1}", name=f"Item {i}", price=i * 10) for i in range(limit)]


@app.post("/items", status_code=status.HTTP_204_NO_CONTENT)
def create_item(item: Annotated[Item, Body()]): ...


@app.get("/items/{item_id}")
def read_item(item_id: Annotated[str, Path(min_length=2, max_length=8)]) -> Item:
    return Item(id=item_id, name="Foo", price=42)
