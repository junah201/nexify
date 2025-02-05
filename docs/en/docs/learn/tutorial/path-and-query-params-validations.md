# Path and Query Parameters and Validation

You can add validation for both path and query parameters.

## String Validation: Minimum & Maximum Length

{* ../../docs_src/path_and_query_params_validations/tutorial001.py hl[8] *}

✅ Allowed: `/items/ab`, `/items/12345678`

❌ Not Allowed: `/items/a` (too short), `/items/123456789` (too long)

In this case, `item_id` is constrained to a minimum of 2 characters and a maximum of 8 characters.

## String Validation: Regular Expressions

You can define a regular expression `pattern` that the parameter should match:

{* ../../docs_src/path_and_query_params_validations/tutorial002.py hl[8,12] *}

✅ Allowed: `/users/test@example.com`, `/users/user123@domain.co.kr`

❌ Not Allowed: `/users/invalid-email`, `/users/user@domain`

In this case, the `email` parameter is validated to ensure it follows an email format.

If an invalid `email` is provided, a 422 response like the following will be returned:

```JSON
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": [
        "path",
        "email"
      ],
      "msg": "String should match pattern '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'",
      "input": "invalid-email",
      "ctx": {
        "pattern": "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
      }
    }
  ]
}
```

## Numeric Validation: Greater Than, Greater Than or Equal, Less Than, Less Than or Equal

{* ../../docs_src/path_and_query_params_validations/tutorial003.py hl[9] *}

- `gt`: `G`reater `t`han
- `ge`: `G`reater than or `e`qual
- `lt`: `L`ess `t`han
- `le`: `L`ess than or `e`qual

## Numeric Validation: Maximum Number of Digits

{* ../../docs_src/path_and_query_params_validations/tutorial004.py hl[9] *}

✅ Allowed: `/items/123` (3 digits)

❌ Not Allowed: `/items/1000000` (7 digits)


## 문서화

![Swagger UI with max and min length](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-validations/01-swagger-ui.png)

Both maximum and minimum lengths are displayed in Swagger UI (and ReDoc).

![Swagger UI with pattern](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-validations/02-swagger-ui.png)

Additionally, various data validation rules are automatically included in Swagger UI (and ReDoc).

## Additional Data Validation Options

- `multiple_of`: Value must be a multiple of this.
- `allow_inf_nan`: Allow `inf`, `-inf`, `nan`.
- `decimal_places`: Maximum number of decimal places allowed for numbers.
