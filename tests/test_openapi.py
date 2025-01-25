import json
from typing import Annotated

import pytest
from nexify import Body, Nexify, Path, Query
from pydantic import BaseModel


def test_basic_openapi():
    app = Nexify(title="Nexify", version="0.1.0", description="A simple API")

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
    app = Nexify(
        title="Nexify",
        version="0.1.0",
        description="A simple API",
        openapi_tags=[
            {
                "name": "items",
                "description": "Operations on items",
            }
        ],
    )

    @app.get("/items", tags=["items"])
    def get_items(limit: Annotated[int, Query()]): ...

    @app.get("/items/{item_id}", tags=["items"])
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
        "tags": [{"name": "items", "description": "Operations on items"}],
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get Items",
                    "tags": ["items"],
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
                    "tags": ["items"],
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


def test_openapi_with_body():
    app = Nexify(title="Nexify", version="0.1.0", description="A simple API")

    class Item(BaseModel):
        name: str

    @app.post("/items")
    def create_item(
        item: Annotated[
            Item,
            Body(),
        ],
    ): ...

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
        "servers": [],
        "components": {
            "schemas": {
                "Item": {
                    "properties": {"name": {"title": "Name", "type": "string"}},
                    "required": ["name"],
                    "title": "Item",
                    "type": "object",
                }
            }
        },
        "paths": {
            "/items": {
                "post": {
                    "summary": "Create Item",
                    "operationId": "create_item_items_post",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Item"}}},
                    },
                }
            }
        },
    }


@pytest.mark.parametrize(
    "openapi_extra",
    [
        ({"x-aperture-labs-portal": "blue"}),
    ],
)
def test_openapi_with_openapi_extra(openapi_extra):
    app = Nexify(title="Nexify", version="0.1.0", description="A simple API", openapi_extra=openapi_extra)

    @app.get("/items", openapi_extra=openapi_extra)
    def get_items(): ...

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
        "servers": [],
        "paths": {
            "/items": {
                "get": {"summary": "Get Items", "operationId": "get_items_items_get", "x-aperture-labs-portal": "blue"}
            }
        },
    }


def test_openapi_with_summary_and_description():
    app = Nexify(
        title="Nexify",
        version="0.1.0",
        description="A simple API",
        summary="A simple API",
    )

    @app.get("/items", summary="Get Items", description="Get items by limit")
    def get_items(
        limit: Annotated[
            int,
            Query(
                description="The number of items to return",
            ),
        ],
    ): ...

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "summary": "A simple API", "description": "A simple API"},
        "servers": [],
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get Items",
                    "description": "Get items by limit",
                    "operationId": "get_items_items_get",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer", "description": "The number of items to return"},
                            "description": "The number of items to return",
                        }
                    ],
                }
            }
        },
    }


def test_openapi_with_deprecated():
    app = Nexify(
        title="Nexify",
        version="0.1.0",
        description="A simple API",
    )

    @app.get("/items", deprecated=True)
    def get_items(): ...

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
        id: Annotated[
            int,
            Query(
                deprecated=True,
            ),
        ],
    ): ...

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
        "servers": [],
        "paths": {
            "/items": {"get": {"summary": "Get Items", "operationId": "get_items_items_get", "deprecated": True}},
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
                        },
                        {
                            "name": "id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer", "deprecated": True},
                            "deprecated": True,
                        },
                    ],
                }
            },
        },
    }


def test_openapi_with_example():
    app = Nexify(
        title="Nexify",
        version="0.1.0",
        description="A simple API",
    )

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

    class Item(BaseModel):
        name: str

    @app.post("/items")
    def create_item(
        item: Annotated[
            Item,
            Body(
                openapi_examples={
                    "example 1": {
                        "value": {"name": "foo"},
                        "summary": "A simple item",
                    }
                },
            ),
        ],
    ): ...

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
        "servers": [],
        "components": {
            "schemas": {
                "Item": {
                    "properties": {"name": {"title": "Name", "type": "string"}},
                    "required": ["name"],
                    "title": "Item",
                    "type": "object",
                }
            }
        },
        "paths": {
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
            "/items": {
                "post": {
                    "summary": "Create Item",
                    "operationId": "create_item_items_post",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Item"},
                                "examples": {"example 1": {"value": {"name": "foo"}, "summary": "A simple item"}},
                            }
                        },
                    },
                }
            },
        },
    }


def test_openapi_with_duplicated_operate_id():
    app = Nexify(
        title="Nexify",
        version="0.1.0",
        description="A simple API",
    )

    @app.get("/items", operation_id="get_items")
    def get_items(): ...

    @app.get("/items/{item_id}", operation_id="get_items")
    def get_item(item_id: Annotated[str, Path()]): ...

    with pytest.warns(UserWarning, match=r"Duplicate Operation ID .+ for function .+( at .+)?"):
        app.openapi()
