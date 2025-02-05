# Query Parameters

You can declare "query" parameters by defining function parameters with `Query()`.

{* ../../docs_src/query_params/tutorial001.py hl[12] *}

A query parameter is a key-value pair appended to a URL after a question mark (`?`).

Multiple query parameters can be included by separating them with an ampersand (&), forming a single string.

For example, in the following URL:

예를 들어, 아래의 URL에서

```
/items?skip=0&limit=10
```

The query parameters are:

- skip: with a value of `0`
- limit: with a value of `10`

As they are part of the URL, they are "naturally" strings.

But when you declare them with Python types (in the example above, as `int`), they are converted to that type and validated against it.

All the same process that applied for path parameters also applies for query parameters:

- Editor support: error checks, autocompletion, etc.
- Data "<abbr title="converting the string that comes from an HTTP request into Python data">parsing</abbr>"
- Data validation
- API annotation and automatic documentation

## Default Values

Query parameters are not fixed parts of the path, meaning they can be optional and have default values.

/// info
Unlike query parameters, path parameters cannot be optional or have default values.
///

In this case, `skip` has a default value of `0`, and `limit` has a default value of `10`.

So, going to `/items` would be teh same as going to `/items?skip=0&limit=10`.

But if you go to `/items?skip=20`

The query parameter values in your function will be:

- `skip=20`: because you set it in the URL
- `limit=10`: because that was the default value

## Declaring Default Values in Different Ways

You can also set default values by passing the default parameter inside `Query()` within `Annotated`.

{* ../../docs_src/query_params/tutorial002.py hl[12] *}

In this case, `skip` defaults to `0`, and `limit` defaults to `10`.

Using this way allows you to bypass Python's restriction that parameters without default values must precede those with default values, which can be useful in some situations.

---

Alternatively, you can set default values using the `default_factory` parameter inside `Query()` within `Annotated`.

{* ../../docs_src/query_params/tutorial003.py hl[16:17] *}

The `default_factory` is **extremely useful** in various situations:

- When a dynamic value is needed for each request: for example, `datetime.now()` returns a different value each time it is called.
- When using mutable objects as default values: instead of manually checking for None, you can set `default_factory=list` or `default_factory=dict` to ensure a new list or dictionary is created for each request.
- When providing computed default values: if a default value needs to be derived from logic, wrapping it in a function and passing it to `default_factory` keeps the code clean.

## Data Validation

{* ../../docs_src/query_params/tutorial001.py hl[12] *}

If you go to `/items?skip=foo`, you will see a `422` response like this:

```JSON
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "query",
        "skip"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "foo"
    }
  ]
}
```

Just like in the path parameters tutorial, since `"foo"` cannot be converted to an `int`, an internal Pydantic-based validation error occurs, and Nexify returns a 422 response with a detailed error message.

## Documentation

And go to `/docs`, you will see the following Swagger UI:

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/query-params/01-swagger-ui.png)

/// check | 확인
Since **Nexify** automatically generates API documentation based on Python type hints, you can see that the path parameter is correctly documented as an `int` type. Their default values are also clearly displayed as 0 and 10.
///

## Required Query Parameters

Query parameters with default values are always "optional". To make a query parameter "required", simply do not provide a default value.

{* ../../docs_src/query_params/tutorial004.py hl[12] *}

if you go to `/items` without query parameters, you will receive a 422 response like this:

```JSON
{
  "detail": [
    {
      "loc": ["query", "skip"],
      "msg": "Field required",
      "type": "missing",
      "input": null
    },
    {
      "loc": ["query", "limit"],
      "msg": "Field required",
      "type": "missing",
      "input": null
    }
  ]
}
```

Since no default values are provided, skip and limit are "required" query parameters, and their absence triggers a validation error.

Additionally, the documentation clearly indicates that these parameters are "required".

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/query-params/02-swagger-ui.png)
