# Body - Fields

Just like `Path` and `Query`, you can use Pydantic's `Field` in `Body` to declare validation rules within a model and provide additional metadata. This allows you to define validation for request bodies more clearly in your API.

## import `Field`

First, you have to import it:

{* ../../docs_src/body_validation/tutorial001.py hl[4] *}

## Declaring Model Attributes

You can then use `Field` with model attributes:

{* ../../docs_src/body_validation/tutorial001.py hl[13:17,21:24,28:31] *}

You can use the same properties as in `Path` and `Query`, including:

- `gt`, `ge`, `lt`, `le`: Constraints for numeric values (gt=0 means greater than 0, ge=0 means greater than or equal to 0)
- `min_length`, `max_length`: Constraints for string length (min_length=2, max_length=50)
- `regex`: String validation using regular expressions (regex="^[a-zA-Z0-9_-]+$")

In addition to these, various other options are available. For more details, refer to the Pydantic official documentation.

## Adding Extra Information Using `Body()`

You can use `openapi_examples` inside `Body()` to define example values that will be displayed in the API documentation.

{* ../../docs_src/body_validation/tutorial002.py hl[21:32] *}

In this case, you can see the example values in the API documentation.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/body-fields/01-swagger-ui-example.png)

/// info
You can also set a example value using `Field(..., example=1234)`, but if you want to add more detailed examples to your OpenAPI documentation, it is recommended to use `openapi_examples` inside `Body()`.
///
