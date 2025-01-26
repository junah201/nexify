import json
from collections.abc import Mapping
from typing import Annotated, Any

from nexify import status
from nexify.encoders import jsonable_encoder


class Response: ...


class HttpResponse(Response):
    """
    Response class that returns a valid API Gateway response.
    It is not only for HTTP API Gateway, but also for REST API Gateway.
    """

    media_type: str | None = None
    charset: str = "utf-8"
    status_code = status.HTTP_200_OK

    def __init__(
        self,
        content: Any = None,
        status_code: int | None = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
    ):
        self.status_code = status_code or self.status_code
        self.media_type = media_type or self.media_type
        self.headers = headers or {}
        self.content = content
        self.response = self.render()

    def render(self) -> dict[str, Any]:
        content = jsonable_encoder(self.content)
        content = self.content_converter(content)

        result = {
            "statusCode": self.status_code,
            "body": content,
            "headers": {
                "content-type": f"{self.media_type}; charset={self.charset}",
            },
        }
        if self.media_type is None and content is None:
            del result["body"]  # type: ignore[union-attr]
            del result["headers"]["content-type"]  # type: ignore[union-attr]
        result["headers"].update(self.headers)  # type: ignore[union-attr]
        return result

    def content_converter(self, content: Any) -> Any:
        return self.content


class JSONResponse(HttpResponse):
    media_type = "application/json"

    def __init__(
        self,
        content: Any = None,
        status_code: int | None = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
    ):
        super().__init__(content=content, status_code=status_code, headers=headers, media_type=media_type)

    def content_converter(self, content: Any) -> Any:
        return json.dumps(content)


class PlainTextResponse(HttpResponse):
    media_type = "text/plain"

    def __init__(
        self,
        content: Any = None,
        status_code: int | None = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
    ):
        super().__init__(content=content, status_code=status_code, headers=headers, media_type=media_type)

    def content_converter(self, content: Any) -> Any:
        return str(content)


class HTMLResponse(HttpResponse):
    media_type = "text/html"

    def __init__(
        self,
        content: Any = None,
        status_code: int | None = status.HTTP_200_OK,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
    ):
        super().__init__(content=content, status_code=status_code, headers=headers, media_type=media_type)

    def content_converter(self, content: Any) -> Any:
        return str(content)


class RedirectResponse(HttpResponse):
    def __init__(
        self,
        url: str,
        content: Annotated[None, "This is not used. It is only for compatibility."] = None,
        status_code: int | None = status.HTTP_307_TEMPORARY_REDIRECT,
        headers: Mapping[str, str] | None = None,
    ):
        self.url = url
        headers = headers or {}
        headers["location"] = url  # type: ignore
        super().__init__(status_code=status_code, headers=headers)
