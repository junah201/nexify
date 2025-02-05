from typing import Annotated

from nexify import Nexify, Path

app = Nexify()


EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


@app.get("/users/{email}")
def get_user(email: Annotated[str, Path(pattern=EMAIL_REGEX)]) -> dict:
    return {"email": email}
