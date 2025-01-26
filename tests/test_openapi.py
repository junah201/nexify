import json
from typing import Annotated

import pytest
from nexify import Body, Nexify, Path, Query
from pydantic import BaseModel, Field


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
                    "tags": ["items"],
                    "summary": "Get Items",
                    "operationId": "get_items_items_get",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {},
                                },
                            },
                        }
                    },
                }
            },
            "/items/{item_id}": {
                "get": {
                    "tags": ["items"],
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
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
                    },
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
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
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
                "get": {
                    "summary": "Get Items",
                    "operationId": "get_items_items_get",
                    "x-aperture-labs-portal": "blue",
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
                    },
                }
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
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
                    },
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
                description="Please use item_id instead",
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
                    "deprecated": True,
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
                    },
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
                        },
                        {
                            "name": "id",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "integer",
                                "description": "Please use item_id instead",
                                "deprecated": True,
                            },
                            "description": "Please use item_id instead",
                            "deprecated": True,
                        },
                    ],
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
                    },
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
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
                    },
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
                    "responses": {
                        "200": {"description": "Successful Response", "content": {"application/json": {"schema": {}}}}
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


def test_openapi_with_response():
    app = Nexify(
        title="Nexify",
        version="0.1.0",
        description="A simple API",
    )

    class Item(BaseModel):
        name: str
        price: Annotated[float, Field(description="The price of the item", ge=0)]

    @app.get("/items")
    def get_items() -> list[Item]: ...

    @app.get("/items/{item_id}", response_description="Successful Response so that it returns an Item")
    def get_item(item_id: Annotated[str, Path()]) -> Item: ...

    with open("openapi.json", "w") as f:
        f.write(json.dumps(app.openapi(), indent=2))

    assert app.openapi() == {
        "openapi": "3.1.0",
        "info": {"title": "Nexify", "version": "0.1.0", "description": "A simple API"},
        "servers": [],
        "components": {
            "schemas": {
                "Item": {
                    "properties": {
                        "name": {"title": "Name", "type": "string"},
                        "price": {
                            "description": "The price of the item",
                            "minimum": 0.0,
                            "title": "Price",
                            "type": "number",
                        },
                    },
                    "required": ["name", "price"],
                    "title": "Item",
                    "type": "object",
                }
            }
        },
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get Items",
                    "operationId": "get_items_items_get",
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Item"}}
                                }
                            },
                        }
                    },
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
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful Response so that it returns an Item",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"},
                                },
                            },
                        }
                    },
                }
            },
        },
    }
