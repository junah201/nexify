from typing import Annotated

from nexify import Nexify, Query

app = Nexify()

fake_items_db = [{"name": "Foo"}, {"name": "Bar"}, {"name": "Baz"}]


@app.get("/items")
def read_items(skip: Annotated[int, Query()], limit: Annotated[int, Query()]):
    return fake_items_db[skip : skip + limit]
