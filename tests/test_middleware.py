import json

from nexify import Nexify
from nexify.middleware import Middleware
from nexify.responses import JSONResponse


def test_basic_middleware():
    def custom_my_middleware(route, event, context, call_next):
        response = call_next(event, context)
        response.headers["x-custom-header"] = "Custom Value"
        return response

    app = Nexify(middlewares=[custom_my_middleware])

    @app.get("/items")
    def read_items():
        return JSONResponse(content={"items": [{"name": "Item One"}, {"name": "Item Two"}]})

    response = read_items({}, {})

    assert response == {
        "statusCode": 200,
        "body": json.dumps({"items": [{"name": "Item One"}, {"name": "Item Two"}]}),
        "headers": {"content-type": "application/json; charset=utf-8", "x-custom-header": "Custom Value"},
    }


def test_decorator_middleware(app):
    @app.middleware
    def custom_my_middleware(route, event, context, call_next):
        response = call_next(event, context)
        response.headers["x-custom-header"] = "Custom Value"
        return response

    @app.get("/items")
    def read_items():
        return JSONResponse(content={"items": [{"name": "Item One"}, {"name": "Item Two"}]})

    response = read_items({}, {})

    assert response["headers"] == {
        "content-type": "application/json; charset=utf-8",
        "x-custom-header": "Custom Value",
    }


def test_class_middleware(app):
    class CustomMiddleware(Middleware):
        def __call__(self, route, event, context, call_next):
            response = call_next(event, context)
            response.headers["x-custom-header"] = "Custom Value"
            return response

    app.add_middleware(CustomMiddleware())

    @app.get("/items")
    def read_items():
        return JSONResponse(content={"items": [{"name": "Item One"}, {"name": "Item Two"}]})

    response = read_items({}, {})

    assert response["headers"] == {
        "content-type": "application/json; charset=utf-8",
        "x-custom-header": "Custom Value",
    }
