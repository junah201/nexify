# Nexify

<p align="center">
<a href="https://pypi.org/project/nexify" target="_blank">
    <img src="https://img.shields.io/pypi/v/nexify?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/nexify" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/nexify.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

---

**Documentation**: <a href="https://nexify.junah.dev" target="_blank">https://nexify.junah.dev</a>

**Source Code**: <a href="https://github.com/junah201/nexify" target="_blank">https://github.com/junah201/nexify</a>

---


Nexify is a lightweight web framework for building APIs on AWS Lambda's Python runtime based on standard Python type hints.

The key features are:

- 🚀 **Automatic Parsing**: Automatically parses <a href="https://aws.amazon.com/pm/lambda" target="_blank">AWS Lambda</a>'s Event and Context objects.
- 🔍 **Data Validation**: Validate user's request and response using <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a>.
- 📜 **OpenAPI Documentation**: Generates API documentation with <a href="https://github.com/swagger-api/swagger-ui" class="external-link" target="_blank">Swagger UI</a> and <a href="https://github.com/Redocly/redoc" class="external-link" target="_blank">ReDoc</a>.
- ☁️ **Deployment Automation**: Deploy <a href="https://aws.amazon.com/pm/lambda" target="_blank">AWS Lambda</a> and related infrastructure with a simple command.

## Requirements

**Nexify** requires the following libraries:

- <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a> for data validation and OpenAPI documentation.
- <a href="https://boto3.amazonaws.com/v1/documentation/api/latest/index.html" class="external-link" target="_blank">Boto3</a> for AWS deployment. (Only required in local development, not in production.)

## Installation

First, set up a virtual environment, then install **Nexify**:

<div class="termy">

```console
$ pip install "nexify[cli]"

---> 100%
```

</div>

**Note**: Some terminal environments require quoting "nexify[cli]" for correct installation.

## Usage

### Creating a Project

<div class="termy">

```console
$ nexify init
Enter the project name: myapp
🎉 Project myapp created at 'C:\Users\junah\Desktop\myapp'
$ cd myapp
```

</div>

Running `nexify init` command generates a `main.py` file, a `nexify.json` configuration file, and etc.

- Example `main.py`:

```py
from typing import Annotated

from nexify import Body, Nexify, Path, Query, status
from pydantic import BaseModel, Field

app = Nexify(title="My Nexify API", version="0.1.0")


class Item(BaseModel):
    id: str
    name: str
    price: Annotated[int, Field(ge=0)]


@app.get("/items")
def read_items(limit: Annotated[int, Query(default=10)]) -> list[Item]:
    return [Item(id=f"{i + 1}", name=f"Item {i}", price=i * 10) for i in range(limit)]


@app.post("/items", status_code=status.HTTP_204_NO_CONTENT)
def create_item(item: Annotated[Item, Body()]): ...


@app.get("/items/{item_id}")
def read_item(item_id: Annotated[str, Path(min_length=2, max_length=8)]) -> Item:
    return Item(id=item_id, name="Foo", price=42)
```

- Example `nexify.json`:

```json
{
  "service": "myapp",
  "provider": {
    "name": "aws",
    "runtime": "python3.10",
    "region": "ap-northeast-2",
    "profile": "default",
    "logRetentionInDays": 14,
    "architecture": "x86_64",
    "memorySize": 128,
    "timeout": 10,
    "stage": "prod",
    "environment": { "YOUR_CUSTOM_ENV": "${env:YOUR_CUSTOM_ENV}" },
    "iamRoleStatements": [
      { "Effect": "Allow", "Action": ["s3:*"], "Resource": "*" }
    ]
  },
  "package": {
    "include": ["main.py"],
    "exclude": [".venv/**", ".git/**", ".gitignore"],
    "pipCmdExtraArgs": [""]
  },
  "resources": {
    "Resources": {
      "APIGatewayRestAPI": {
        "Type": "AWS::ApiGateway::RestApi",
        "Properties": {
          "Name": "myapp-API",
          "EndpointConfiguration": { "Types": ["EDGE"] },
          "Policy": "",
          "Description": "API for myapp"
        }
      }
    }
  }
}
```

### Deploying

<div class="termy">

```console
$ nexify deploy
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
    - GET   https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items
    - POST  https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items
    - GET   https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items/{item_id}


Functions:
    - read_items
    - create_item
    - read_item
```

</div>

Once deployment is complete, API endpoints are generated.

### Checking the API

Open the following URL in a browser to check the API response:

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items/12
```

**Note**: Use the URL displayed after executing `nexify deploy` command.

Response example:

```json
{"id":"12","name":"Foo","price":42}
```

---

Congratulations 🎉 You have already created an API.

- The `/items` and `/items/{item_id}` endpoints can now receive HTTP requests.
- The `/items` endpoint handles `GET` and `POST` requests, while `/items/{item_id}` handles `GET` requests.
- The `/items` endpoint has a `int` query parameter `limit` with a default value of `10`.
- The `/items/{item_id}` endpoint has a `str` path parameter `item_id` with a length constraint between `2` and `8` characters.

Nexify uses <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a> internally to validate the input and output data.

### Swagger UI

Now go to <a href="https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs" class="external-link" target="_blank">https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs</a>.

**Note**: Please use the output URL after running the `nexify deploy` command.

You will see the automatic interactive API documentation (provided by <a href="https://github.com/swagger-api/swagger-ui" class="external-link" target="_blank">Swagger UI</a>):

![Swagger UI](https://nexify.junah.dev/img/index/index-01-swagger-ui-simple.png)

### ReDoc

And now, go to <a href="https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc" class="external-link" target="_blank">https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc</a>.

**Note**: Please use the output URL after running the `nexify deploy` command.

You will see the automatic interactive API documentation (provided by <a href="https://github.com/Redocly/redoc" class="external-link" target="_blank">ReDoc</a>):

![ReDoc](https://nexify.junah.dev/img/index/index-02-redoc-simple.png)

### Summary

With Nexify, you can easily develop APIs on <a href="https://aws.amazon.com/pm/lambda" target="_blank">AWS Lambda</a> using standard Python type hints.

- 🔍 **Data Validation**: Uses Pydantic for input and response validation.
    - Automatically generates clear errors for invalid data.
    - Supports validation for nested JSON objects.
- 📦 **Automatic Parsing**: Extracts body, pathParameters, queryStringParameters, and more from the Event object.
- 🔄 **Response Conversion**: Supports conversion of standard Python types (str, int, float, bool, list) as well as datetime, UUID, dataclass, and more.
- 📜 **OpenAPI Documentation**: Supports Swagger UI and ReDoc.
- ☁️ **Deployment Automation**: Deploy AWS Lambda with a single nexify deploy command.

## License

This project is licensed under the terms of the MIT license.
