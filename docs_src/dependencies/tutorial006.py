from typing import Annotated

from nexify import Depends, Header, Nexify
from nexify.exceptions import HTTPException


def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")


app = Nexify(dependencies=[Depends(verify_token), Depends(verify_key)])


@app.get("/items")
def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
