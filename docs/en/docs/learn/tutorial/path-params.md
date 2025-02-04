# Path Parameters

You can declare path "parameters" with the same syntax used by Python format strings:

{* ../../docs_src/path_params/tutorial001.py hl[8:9] *}

The value of the path parameter `item_id` will be passed to your function as the argument `item_id`.

Additionally, `Path()` inside `Annotated` indicates that this function argument is a path parameter.

After deploying this example, and go to `/items/foo`, you will see a response of:

```JSON
{"item_id":"foo"}
```

## Various Types of Path Parameters

Path parameters can be declared not only as `str` but also as `int`, `float`, or `bool` types.

{* ../../docs_src/path_params/tutorial002.py hl[9] *}

In this case, `item_id` is declared as an `int`.

## Data <abbr title="also known as: serialization, parsing, marshalling">Conversion</abbr>

Now, go to `/items/3`, you will see the a response of:

```JSON
{"item_id":3}
```

/// check
Notice that the value your function received (and returned) is `3`, as a Python `int`, not a string `"3"`.

This is because **Nexify** automatically "parses" the path parameter based on the declared type (`int`). That is, the string `"3"` is converted into a Python int of `3`.
///


## Data Validation

But if you go to the browser at `/items/foo`, you will see a nice 422 HTTP error of:

```JSON
{
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["path", "item_id"],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "foo",
        }
    ]
}
```

The 422 status code means `"Unprocessable Entity."` It indicates that the request is valid, but the provided data does not match the expected format.

In this case, when requesting `/items/foo`, the string `"foo"` cannot be converted to an `int`. As a result, an internal Pydantic-based validation error occurs, and **Nexify** returns a 422 response with a detailed error message.

The same error would appear if you provided a `float` instead of an `int`, as in: `/items/3.14`

/// check
So, with the same Python type declaration, **Nexify** gives you data validation.

Notice that the error also clearly states exactly the point where the validation didn't pass.

This is incredibly helpful while developing and debugging code that interacts with your API.
///

### Benefits of Data Validation

- **Automatic validation**: Simply declaring the type of a path parameter ensures automatic data validation.
- **Clear error messages**: If invalid input is provided, a detailed error message explains exactly what data is invalid, making development and debugging easier.

All data validation is performed internally by Pydantic, allowing you to leverage its extensive features.

More details can be found in<a href="https://nexify.junah.dev/tutorial/path-params-with-validation" class="internal-link">Path Parameters and Data Validation tutorial</a>.

## Documentation

And go to `/docs`, you will see the following Swagger UI:

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/path-params/01-swagger-ui.png)

/// check
Since **Nexify** automatically generates API documentation based on Python type hints, you can see that the path parameter is correctly documented as an `int` type.
///

## Path Matching Order

For example, you can define both `items/all` (retrieving all items) and `items/{item_id}` (retrieving a specific item).

{* ../../docs_src/path_params/tutorial003.py hl[8,13] *}

In **Nexify**, API paths are correctly mapped as long as they have unique function names, regardless of the order of declaration.

## Multiple Path Parameters

You can also declare multiple path parameters. For example, you can create a path that includes both `item_id` and `user_id`.

{* ../../docs_src/path_params/tutorial004.py hl[8:9] *}

In this case, `item_id` and `user_id` are declared as `int` and `str`, respectively.

## Recap

With **Nexify**, you can build powerful APIs simply by using Python type hints.

- Editor support: error checks, autocompletion, etc.
- Data "<abbr title="converting the string that comes from an HTTP request into Python data">parsing</abbr>"
- Data validation
- API annotation and automatic documentation

For advanced validation and additional features, refer to the Path Parameters and Data Validation tutorial.

More details about data validation and additional features can be found in<a href="https://nexify.junah.dev/tutorial/path-params-with-validation" class="internal-link">Path Parameters and Data Validation tutorial</a>.