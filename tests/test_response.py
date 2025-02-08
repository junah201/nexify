import json
from typing import Annotated

from nexify import status
from nexify.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


def test_no_response_field(app):
    @app.get("/no-response-field-with-json-response")
    def no_response_field_with_json_response():
        return {
            "summary": "No Response Field",
            "description": "This endpoint has no response field",
        }

    @app.get("/no-response-field-without-response")
    def no_response_field_without_response():
        return "This endpoint has no response field"

    @app.get("/no-response-field-with-pydantic-response")
    def no_response_field_with_pydantic_response():
        class TestResponse(BaseModel):
            summary: Annotated[str, Field()]
            description: Annotated[str, Field()]

        return TestResponse(summary="No Response Field", description="This endpoint has no response field")

    response = no_response_field_with_json_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": '{"summary": "No Response Field", "description": "This endpoint has no response field"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }

    response = no_response_field_without_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": '"This endpoint has no response field"',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }

    response = no_response_field_with_pydantic_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": '{"summary": "No Response Field", "description": "This endpoint has no response field"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }


def test_json_response_class(app):
    @app.get("/json-response")
    def json_response():
        return {
            "summary": "JSON Response",
            "description": "This endpoint has JSON response",
        }

    class TestResponse(BaseModel):
        summary: str
        description: str

    @app.get("/json-response-with-pydantic-response")
    def json_response_with_pydantic_response() -> TestResponse:
        return TestResponse(summary="JSON Response", description="This endpoint has JSON response")

    class TestTypedDictResponse(TypedDict):
        summary: str
        description: str

    @app.get("/json-response-with-typed-dict-response")
    def json_response_with_typed_dict_response() -> TestTypedDictResponse:
        return {
            "summary": "JSON Response",
            "description": "This endpoint has JSON response",
        }

    response = json_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": '{"summary": "JSON Response", "description": "This endpoint has JSON response"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }

    response = json_response_with_pydantic_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": '{"summary": "JSON Response", "description": "This endpoint has JSON response"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }

    response = json_response_with_typed_dict_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": '{"summary": "JSON Response", "description": "This endpoint has JSON response"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }


def test_plain_text_response_class(app):
    @app.get("/text-response", response_class=PlainTextResponse)
    def text_response():
        return "Hello, World!"

    response = text_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": "Hello, World!",
        "headers": {"content-type": "text/plain; charset=utf-8"},
    }


def test_plain_text_response_class_with_response_field(app):
    @app.get("/text-response-with-invalid-response-field", response_class=PlainTextResponse)
    def text_response_with_invalid_int_response_field() -> int:
        return {
            "summary": "Invalid Response Field",
            "description": "This endpoint has invalid response field",
        }  # type: ignore

    class TestResponse(BaseModel):
        summary: str
        description: str

    @app.get("/text-response-with-invalid-response-field", response_class=PlainTextResponse)
    def text_response_with_pydantic_response_field() -> TestResponse:
        return TestResponse(
            summary="valid Response Field",
            description="This endpoint has valid response field",
        )

    res = text_response_with_invalid_int_response_field({}, {})
    assert res == {
        "statusCode": 500,
        "headers": {"content-type": "application/json; charset=utf-8"},
        "body": json.dumps({"detail": "Internal Server Error"}),
    }

    response = text_response_with_pydantic_response_field({}, {})
    assert response == {
        "statusCode": 200,
        "body": "{'summary': 'valid Response Field', 'description': 'This endpoint has valid response field'}",
        "headers": {"content-type": "text/plain; charset=utf-8"},
    }


def test_html_response(app):
    @app.get("/html-response", response_class=HTMLResponse)
    def html_response():
        return "<html><body><h1>Hello, World!</h1></body></html>"

    response = html_response({}, {})
    assert response == {
        "statusCode": 200,
        "body": "<html><body><h1>Hello, World!</h1></body></html>",
        "headers": {"content-type": "text/html; charset=utf-8"},
    }


def test_redirect_response(app):
    @app.get("/redirect-response", response_class=RedirectResponse)
    def redirect_response():
        return RedirectResponse(url="https://google.com")

    response = redirect_response({}, {})
    assert response == {
        "statusCode": status.HTTP_307_TEMPORARY_REDIRECT,
        "headers": {"location": "https://google.com"},
    }


def test_response_with_status_code(app):
    @app.post("/response-with-status-code", status_code=status.HTTP_201_CREATED)
    def response_with_status_code():
        return {"status": "created"}

    response = response_with_status_code({}, {})
    assert response == {
        "statusCode": status.HTTP_201_CREATED,
        "body": '{"status": "created"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }
