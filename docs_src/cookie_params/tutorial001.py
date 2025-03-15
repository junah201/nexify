from typing import Annotated

from nexify import Cookie, Nexify

app = Nexify()


@app.get("/cookies")
def read_cookies(session_id: Annotated[str, Cookie()]) -> dict:
    return {"Session-ID": session_id}
