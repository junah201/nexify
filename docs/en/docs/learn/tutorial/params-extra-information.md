# Parameters and Extra Information

You can add additional information for path and query parameters. It is mainly seen in Swagger and ReDoc.

## Title and Description

If you want to add a title and description to a specific path or query parameter, you can use `title` and `description`.

{* ../../docs_src/path_and_query_params_extra_information/tutorial001.py hl[13:14] *}

In this case, you can see the description provided for `item_id`.

![Swagger UI Title and Description](https://nexify.junah.dev/img/learn/tutorial/params-extra-information/01-swagger-ui-title-and-description.png)

/// info
The title is displayed only in ReDoc.
///

## Examples (openapi_examples)

{* ../../docs_src/path_and_query_params_extra_information/tutorial002.py hl[13:22] *}

You can see the OpenAPI examples.

![Swagger UI Example](https://nexify.junah.dev/img/learn/tutorial/params-extra-information/02-swagger-ui-example.png)

## Deprecated

If you need to deprecate a path or query parameter without removing it, you can use `deprecated`.

{* ../../docs_src/path_and_query_params_extra_information/tutorial003.py hl[13] *}

In this case, you can see that itemId is marked with a red `deprecated` label, indicating that it is a deprecated query parameter.

![Swagger UI Deprecated](https://nexify.junah.dev/img/learn/tutorial/params-extra-information/03-swagger-ui-deprecated.png)
