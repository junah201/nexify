from nexify import Nexify
from nexify.responses import JSONResponse

app = Nexify()


class MyCustomException(Exception):
    pass


class CustomExceptionHandler:
    def __call__(self, event, _context, exc):
        return JSONResponse(content={"detail": "Custom Internal Server Error"}, status_code=500)


app.add_exception_handler(MyCustomException, CustomExceptionHandler())
