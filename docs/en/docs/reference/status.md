# Status Codes

You can import the `status` module from `nexify`:

```python
from nexify import status
```

It contains a group of named constants (variables) with integer status codes.

For example:

* 200: `status.HTTP_200_OK`
* 403: `status.HTTP_403_FORBIDDEN`
* etc.

It can be convenient to quickly access HTTP status codes in your app, using autocompletion for the name without having to remember the integer status codes by memory.

## Example

```python
from typing import Annotated

from nexify import Body, Nexify, Path, Query, status
from pydantic import BaseModel, Field

app = Nexify(title="My Nexify API", version="0.1.0")


@app.post("/items", status_code=status.HTTP_204_NO_CONTENT)
def create_item(item: Annotated[Item, Body()]): ...
```

::: nexify.status
