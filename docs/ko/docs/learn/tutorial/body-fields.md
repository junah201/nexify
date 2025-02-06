# 본문 - 필드

`Path`와 `Query`에서처럼 `Body`에서도 Pydantic의 `Field`를 사용하여 모델 내의 검증 규칙을 선언하고, 추가적인 메타 정보를 제공할 수 있습니다. 이를 통해 API의 요청 본문(body)에 대한 유효성 검사를 보다 명확하게 정의할 수 있습니다.

## Field import

먼저 `pydantic`에서 `Field`를 import 해야합니다.

{* ../../docs_src/body_validation/tutorial001.py hl[4] *}

## 모델 속성 선언

`Field`를 사용하여 Pydantic 모델의 각 속성을 선언할 수 있습니다.

{* ../../docs_src/body_validation/tutorial001.py hl[13:17,21:24,28:31] *}

`Path` 및 `Query`에서 사용한 것과 동일한 속성들을 사용할 수 있으며, 다음과 같은 속성이 포함됩니다:

- `gt`, `ge`, `lt`, `le`: 숫자 값의 크기 제한 (gt=0은 0보다 커야 함, ge=0은 0 이상)
- `min_length`, `max_length`: 문자열 길이 제한 (min_length=2, max_length=50)
- `regex`: 정규 표현식을 이용한 문자열 검증 (regex="^[a-zA-Z0-9_-]+$")

이것들 이외에도 다양한 것들을 사용할 수 있습니다. 자세한 내용은 Pydantic 공식문서를 참고하세요.

## `Body()`를 사용한 추가 정보

`Body()` 내부에 `openapi_examples`를 활용하여 API 문서에서 표시될 예제 값을 설정할 수 있습니다.

{* ../../docs_src/body_validation/tutorial002.py hl[21:32] *}

API 문서에서 아래와 같이 에제 값을 확인할 수 있습니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/body-fields/01-swagger-ui-example.png)

/// info
`Field(..., example=1234)`와 같은 방식으로 기본 예제 값을 설정할 수도 있지만, OpenAPI 문서에 더 자세한 예제를 추가하려면 `Body()`의 `openapi_examples`를 활용하는 것이 좋습니다.
///
