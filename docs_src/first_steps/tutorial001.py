from nexify import Nexify

app = Nexify()


@app.get("/")
def root():
    return {"message": "Hello World"}
