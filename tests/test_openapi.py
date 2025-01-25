import json
from typing import Annotated

from nexify import Nexify, Path, Query


def test_basic_openapi():
    app = Nexify(title="Nexify", version="0.1.0", description="A simple API")

    with open("openapi.json", "w") as f:
        f.write(json.dumps(app.openapi(), indent=2))

    assert json.dumps(app.openapi(), sort_keys=True) == json.dumps(
        {
            "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
            "openapi": "3.1.0",
            "servers": [],
            "paths": {},
        },
        sort_keys=True,
    )


def test_openapi_with_tags():
    app = Nexify(title="Nexify", version="0.1.0", description="A simple API")

    @app.get("/items")
    def get_items(limit: Annotated[int, Query()]): ...

    @app.get("/items/{item_id}")
    def get_item(
        item_id: Annotated[
            str,
            Path(
                min_length=2,
                openapi_examples={
                    "example 1": {
                        "value": "1234",
                        "summary": "A simple item ID",
                    }
                },
            ),
        ],
    ): ...

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
        "servers": [],
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get Items",
                    "operationId": "get_items_items_get",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                }
            },
            "/items/{item_id}": {
                "get": {
                    "summary": "Get Item",
                    "operationId": "get_item_items__item_id__get",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "minLength": 2},
                            "examples": {"example 1": {"value": "1234", "summary": "A simple item ID"}},
                        }
                    ],
                }
            },
        },
    }
