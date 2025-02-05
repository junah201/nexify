# Request Body

When you need to send data from a client (e.g., a browser) to your API, you send  it as a **request body**.

A request body is the data sent by the client to the API, while the response body is the data the API sends back to the client.

Your API almost always needs to return a response body. But, clients don't always need to send a request body. Sometimes, they may only request a path or include some query parameters without sending a body.

To declare a request body, you use <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a> models with all their power and benefits.

/// info
When sending data, you should use one of the following HTTP methods: `POST` (most common), `PUT`, `DELETE`, or `PATCH`.

Sending a body with a GET request has an undefined behavior in the specifications, nevertheless, it is supported by Nexify, only for very complex/extreme use cases.

As it is discouraged, the interactive docs with Swagger UI won't show the documentation for the body when using `GET`, and proxies in the middle might not support it.
///

## Import Pydantic's `BaseModel`

First, you need to import `BaseModel` from `pydantic`:

{* ../../docs_src/body/tutorial001.py hl[4] *}

## Create your Data Model

Next, you declare your data model as a class that inherits from `BaseModel`.

Use standard Python types for all the attributes:

{* ../../docs_src/body/tutorial001.py hl[7:11] *}

Like query parameters, if a model attribute has a default value, it is optional. Otherwise, it is required. Setting `None` as the default value makes it optional.

For example, this model above declares a JSON "`object`" (or Python `dict`) like:

```JSON
{
  "name": "Foo",
  "description": "An optional description",
  "price": 45.2,
  "tax": 3.5
}
```

Since `description` and `tax` are optional, the following JSON is also valid:

```JSON
{
  "name": "Foo",
  "price": 45.2
}
```

## Declare it as a Parameter

To add the request body to your API, declare it the same way you declared path and query parameters:

{* ../../docs_src/body/tutorial001.py hl[18] *}

Just declare it by putting `Body()` with `Annotated`.

## Data Validation

If you send a request to `/items` with the following body

```JSON
{
  “name": “Foo”,
  “description": “Optional description field”,
  “price": 45.2,
  “tax": “USA TAX”
}
```

In this case, The `tax` should be a `float` but was incorrectly declared as a `str`.
So that you might see a 422 response like this:

```JSON
{
  "detail": [
    {
      "type": "float_parsing",
      "loc": ["body", "item", "tax"],
      "msg": "Input should be a valid number, unable to parse string as a number",
      "input": "USA TAX"
    }
  ]
}
```

Just like in the path and query parameters tutorial, an internal Pydantic-based validation error occurs, and Nexify returns a 422 response with a detailed error message.

## Documentation

The JSON schema of the model is included in the generated OpenAPI schema and is included in the Swagger UI.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/body/01-swagger-ui.png)
