from nexify.responses import JSONResponse


def test_exception_handler(app):
    class MyCustomException(Exception):
        pass

    def custom_exception_handler(event, _context, exc):
        return JSONResponse(content={"detail": "Custom Internal Server Error"}, status_code=500)

    app.add_exception_handler(MyCustomException, custom_exception_handler)

    @app.get("/items")
    def read_items():
        raise MyCustomException()

    response = read_items({}, {})
    assert response == {
        "statusCode": 500,
        "body": '{"detail": "Custom Internal Server Error"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }


def test_decorator_exception_handler(app):
    class MyCustomException(Exception):
        pass

    @app.exception_handler(MyCustomException)
    def custom_exception_handler(event, _context, exc):
        return JSONResponse(content={"detail": "Custom Internal Server Error"}, status_code=500)

    @app.get("/items")
    def read_items():
        raise MyCustomException()

    response = read_items({}, {})
    assert response == {
        "statusCode": 500,
        "body": '{"detail": "Custom Internal Server Error"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }


def test_class_exception_handler(app):
    class MyCustomException(Exception):
        pass

    class CustomExceptionHandler:
        def __call__(self, event, _context, exc):
            return JSONResponse(content={"detail": "Custom Internal Server Error"}, status_code=500)

    app.add_exception_handler(MyCustomException, CustomExceptionHandler())

    @app.get("/items")
    def read_items():
        raise MyCustomException()

    response = read_items({}, {})
    assert response == {
        "statusCode": 500,
        "body": '{"detail": "Custom Internal Server Error"}',
        "headers": {"content-type": "application/json; charset=utf-8"},
    }
