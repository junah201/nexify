import json

from nexify import Nexify
from nexify.responses import JSONResponse


def test_middleware():
    def custom_my_middleware(route, event, context, call_next, **kwargs):
        response = call_next(event, context, **kwargs)
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
