# 경로 및 쿼리 매개변수와 데이터 검증

**Nexify**를 사용하면 경로 매개변수와 쿼리 매개변수에 대한 검증을 추가할 수 있습니다.

## 문자열 검증: 최소 & 최대 길이

{* ../../docs_src/path_and_query_params_validations/tutorial001.py hl[8] *}

✅ 허용됨: `/items/ab`, `/items/12345678`

❌ 허용 안됨: `/items/a` (너무 짧음), `/items/123456789` (너무 김)

위의 예제에서는 `item_id`가 최소 2글자 이상, 최대 8글자 이하만 허용되도록 설정되어 있습니다.

## 문자열 검증: 정규 표현식

정규 표현식을 사용하면 특정 형식의 값만 허용하도록 제한할 수 있습니다.

{* ../../docs_src/path_and_query_params_validations/tutorial002.py hl[8,12] *}

✅ 허용됨: `/users/test@example.com`, `/users/user123@domain.co.kr`

❌ 허용 안됨: `/users/invalid-email`, `/users/user@domain`

위의 예제에서는 `email` 매개변수가 이메일 형식인지 검증합니다.

만약 잘못된 `email`과 함께 요청할 경우, 아래와 같은 422 응답을 확인할 수 있습니다.

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

## 숫자 검증: ~보다 큼, 크거나 같음, 작음, 작거나 같음

{* ../../docs_src/path_and_query_params_validations/tutorial003.py hl[9] *}

- `gt`: ~보다 큼 (`g`reater `t`han)
- `ge`: 크거나 같음 (`g`reater than or `e`qual)
- `lt`: ~보다 작음 (`l`ess `t`han)
- `le`: 작거나 같음 (`l`ess than or `e`qual)

## 숫자 검증: 최대 자릿수 제한

{* ../../docs_src/path_and_query_params_validations/tutorial004.py hl[9] *}

✅ 허용됨: /items/123 (3자리)

❌ 허용 안됨: /items/1000000 (7자리)


## 문서화

![Swagger UI with max and min length](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-validations/01-swagger-ui.png)

최대, 최소 길이는 모두 Swagger UI에 표시됩니다.

![Swagger UI with pattern](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-validations/02-swagger-ui.png)

이뿐만 아니라 다양한 데이터 검증 조건이 자동으로 Swagger UI에 포함됩니다.

## 다양한 데이터 검증 옵션

- `multiple_of`: 특정 값의 배수 제한
- `allow_inf_nan`: 무한대 및 NaN 허용
- `decimal_places`: 소수점 이하 자릿수 제한
