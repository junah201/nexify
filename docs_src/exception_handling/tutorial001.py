from nexify import Nexify
from nexify.responses import JSONResponse


class MyCustomException(Exception):
    pass


app = Nexify()


@app.exception_handler(MyCustomException)
def custom_exception_handler(event, _context, exc):
    return JSONResponse(content={"detail": "Custom Internal Server Error"}, status_code=500)
