# 경로 및 쿼리 매개변수의 추가 정보

**Nexify**를 사용하면 경로 매개변수와 쿼리 매개변수에 대한 추가 정보를 기입할 수 있습니다.

## 제목 (title)과 설명 (description)

만약 특정 경로 매개변수나 쿼리 매개변수에 대해서 제목 또한 설명을 추가하고 싶다면, `title`과 `description`을 사용하면 됩니다.

{* ../../docs_src/path_and_query_params_extra_information/tutorial001.py hl[13:14] *}

`item_id`에 대한 설명이 있는 것을 볼 수 있습니다.

![Swagger UI Title and Description](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-extra-information/01-swagger-ui-title-and-description.png)

/// info
제목은 ReDoc에서만 표시됩니다.
///

## 예시 (openapi_examples)

{* ../../docs_src/path_and_query_params_extra_information/tutorial002.py hl[13:22] *}

OpenAPI 예시가 Swagger 문서에서 볼 수 있는 것을 확인할 수 있습니다.

![Swagger UI Example](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-extra-information/02-swagger-ui-example.png)

## 지원 중단 기능 (deprecated)

만약 특정 경로 매개변수나 쿼리 매개변수를 삭제하지 않고, 지원 중단을 해야한다면, `deprecated`를 사용하면 됩니다.

{* ../../docs_src/path_and_query_params_extra_information/tutorial003.py hl[13] *}

해당 `itemId`가 빨간색 `deprecated` 표시를 통해 지원 중단된 쿼리 매개변수인 것을 확인 할 수 있습니다.

![Swagger UI Deprecated](https://nexify.junah.dev/img/learn/tutorial/path-and-query-params-extra-information/03-swagger-ui-deprecated.png)
