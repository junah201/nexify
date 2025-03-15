from typing import Annotated

from nexify import Body, Nexify
from pydantic import BaseModel

app = Nexify()


class BaseUser(BaseModel):
    username: str
    email: str
    full_name: str | None = None


class UserIn(BaseUser):
    password: str


@app.post("/user")
async def create_user(user: Annotated[UserIn, Body()]) -> BaseUser:
    return user
