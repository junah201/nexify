from typing import Annotated

from nexify import Body, Nexify
from pydantic import BaseModel

app = Nexify()


class UserIn(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    password: str


@app.post("/user")
def create_user(user: Annotated[UserIn, Body()]) -> UserIn:
    return user
