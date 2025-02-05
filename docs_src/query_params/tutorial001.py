from typing import Annotated

from nexify import Nexify
from nexify.params import Query

app = Nexify()

fake_items_db = [{"name": "Foo"}, {"name": "Bar"}, {"name": "Baz"}]


@app.get("/items")
def read_items(skip: Annotated[int, Query()] = 0, limit: Annotated[int, Query()] = 10):
    return fake_items_db[skip : skip + limit]
