from typing import Annotated

from nexify import Header, Nexify

app = Nexify()


@app.get("/items/")
async def read_items(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}
