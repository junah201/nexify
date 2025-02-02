# First Steps

Let's create a project first.

<div class="termy">

```console
$ nexify init
Enter the project name: myapp
🎉 Project myapp created at 'C:\Users\junah\Desktop\myapp'
$ cd myapp
```

</div>

Running `nexify deploy` command will create the `main.py` and `nexify.json` files.

{* ../../docs_src/first_steps/tutorial001.py *}

Copy that to a file `main.py`

/// check
Assuming that the AWS CLI is installed and credentials are registered via the `aws configure` command. If you haven't done this, please refer to the <a href="https://nexify.junah.dev/learn/aws-cli">AWS CLI</a> documentation and complete this step first.
///

<div class="termy">

```console
// Enter the deploy command to proceed with deployment.
$ nexify deploy
// You should soon see output like this:
✔ App imported successfully!
✔ Config loaded successfully!
✔ App analyzed successfully!
✔ Requirements installed successfully!
✔ Lambda functions packaged successfully!
✔ Basic stack created successfully!
✔ Template created successfully!
✔ Stack updated successfully!

🎉 Deployment successful!

Endpoints:
    - GET   https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/


API Docs:
    - openapi    https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/openapi.json
    - Swagger    https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs
    - ReDoc      https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc


Functions:
    - root
```

</div>

## Check It Out

Open your browser at [https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod](https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod)

/// check
Please use the output URL after running the `nexify deploy` command.
///

You will see the JSON response as:
```JSON
{"message": "Hello World"}
```

## Swagger UI

Now go to [https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs](https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs)

/// check
Please use the output URL after running the `nexify deploy` command.
///

You will see the automatic interactive API documentation (provided by <a href="https://github.com/swagger-api/swagger-ui" class="external-link" target="_blank">Swagger UI</a>):

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/first-steps/01-swagger-ui-simple.png)

## ReDoc

And now, go to <a href="https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc" class="external-link" target="_blank">https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc</a>.

/// check
Please use the output URL after running the `nexify deploy` command.
///

You will see the automatic interactive API documentation (provided by <a href="https://github.com/Redocly/redoc" class="external-link" target="_blank">ReDoc</a>):

![ReDoc](https://nexify.junah.dev/img/learn/tutorial/first-steps/02-redoc-simple.png)

## OpenAPI

**Nexify** generates a "schema" with all your API using the **OpenAPI** standard for defining APIs.

#### "Schema"

A "schema" is a definition or description of something. Not the code that implements it, but just an abstract description.

#### API "Schema"

The API schema defines how the structure and data types of the API are described.

This schema definition includes your API paths, the possible parameters they take, etc.

#### Data "Schema"

The term "schema" might also refer to the shape of some data, like a JSON content.

In that case, it would mean the JSON attributes, and data types they have, etc.

#### OpenAPI Schema

OpenAPI defines an API schema for your API. And that schema includes definitions (or "schemas") of the data sent and received by your API using JSON Schema, the standard for JSON data schemas.

#### Check the`openapi.json`

If you are curious about how the raw OpenAPI schema looks like, Nexify automatically generates a JSON (schema) with the descriptions of all your API.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/openapi.json
```

/// check
Please use the output URL after running the `nexify deploy` command.
///

```JSON
{
  "openapi": "3.1.0",
  "info": {
    "title": "Nexify API",
    "version": "0.1.0",
    "description": ""
  },
  "paths": {
    "/": {
      "get": {
        "summary": "Root",
        "operationId": "root__get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
...
```


#### Advantages of OpenAPI

By automatically generating an OpenAPI spec every time the API is deployed, Nexify ensures reliable OpenAPI documentation. These OpenAPI documents offer several advantages:

- Developers can easily review the API's endpoints, request/response specs.
- They can share API specifications clearly with team members or external developers.
- You could also use it to generate code automatically, for clients (frontend, mobile, IoT applications, etc.) that communicate with your API.

## Recap, step by step

### Step 1: import `Nexify`

{* ../../docs_src/first_steps/tutorial001.py hl[1] *}

`Nexify` is a Python class that provides nearly all the functionality needed to build an API in the AWS Lambda Python runtime.

/// info | API Reference
You can check the reference for the Nexify class [here](https://nexify.junah.dev/reference/nexify).
///

### Step 2: Create a `Nexify` "instance"

{* ../../docs_src/first_steps/tutorial001.py hl[3] *}

Here, the `app` variable is an "instance" of the `Nexify` class.

This will be the main point of interaction to create all your API.

### Step 3: Define API Routes

#### Path

"Path" here refers to the last part of the URL starting from the first /.

So, in a URL like:

```
https://example.com/items/foo
```

...the path would be:

```
/items/foo
```

/// info
"Path" is commonly referred to as "Endpoint" or "Route."
///

While building an API, the "path" is the main way to separate "concerns" and "resources".

#### Method

"Method" here refers to the HTTP Method used in the API request.

One of:

- `GET`
- `POST`
- `PUT`
- `DELTE`

...and the more exotic ones:

- `OPTIONS`
- `HEAD`
- `PATCH`
- `TRACE`

We use these HTTP methods to communicate with specific routes.

---

While building an API, you normally use these specific HTTP methods to perform a specific action.

Normally you use:

- `GET` : to read data.
- `POST` : to create data.
- `PUT` : to update data.
- `DELTE` : to delete data.

Other methods like OPTIONS, HEAD, PATCH, and TRACE are less commonly used but may be used for special purposes.

Thus, the combination of "Path" and "Method" defines the specific action, allowing clients to request and receive the data they need.

#### Define a Decorator

{* ../../docs_src/first_steps/tutorial001.py hl[6] *}

`@app.get("/")` tells **Nexify** that the function below is charge of handling requests that go to:

- Path: `/`
- Method: `GET`

/// info | `@dacorator`
That `@something` syntax in Python is called a "decorator"

You put it on top of a function. Like a pretty decorative hat (I guess that's where the term came from).

A "decorator" takes the function below and does something with it.

In our case, this decorator tells Nexify that the function below corresponds to the path `/` with method `GET`.
///

You can also use the other methods:

- `@app.post()`
- `@app.put()`
- `@app.delete()`

And the more exotic ones:

- `@app.options()`
- `@app.head()`
- `@app.patch()`

#### Define the Function

{* ../../docs_src/first_steps/tutorial001.py hl[7] *}

This is a Python function.

It will be called by Nexify whenever it receives a request to the URL "/" using a GET method.

#### Return Value of the Function

{* ../../docs_src/first_steps/tutorial001.py hl[8] *}

You can return a `dict`, `list`, singular values as `str`, `int`, etc.

You can also return Pydantic models (you'll see more about that later).
