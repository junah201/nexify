# 요청 본문 (Body)

클라이언트 (예: 브라우저)에서 API로 데이터를 전송해야 할 때 **요청 본문 (request body)**로 보냅니다.

요청 본문은 클라이언트가 API로 전송하는 데이터이며, 응답 본문 (response body)는 API가 클라이언트로 보내는 데이터입니다.

API는 거의 항상 응답 본문을 반환해야 합니다. 하지만 클라이언트는 항상 요청 본문을 보낼 필요는 없습니다. 때로는 경로(path)만 요청하거나, 일부 쿼리 매개변수(query parameters)만 포함하는 경우도 있으며, 요청 본문을 보내지 않을 수도 있습니다.

요청 본문을 선언하려면, <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a> 모델을 활용하면 됩니다.

/// info
데이터를 전송할 때는 POST(가장 일반적), PUT, DELETE, PATCH 중 하나를 사용해야 합니다.

HTTP 프로토콜에 따르면 GET 요청에 본문을 포함해서 호출하는 것은 허용되지 않습니다. 하지만 Nexify는 매우 특수한 경우를 위해 이를 지원합니다.

하지만 이는 권장되지 않으며, Swagger UI의 자동 문서화에서는 GET 요청 시 본문을 표시하지 않으며, 중간 프록시(proxy)에서 이를 지원하지 않을 수도 있습니다.
///

## Pydantic의 `BaseModel` import

먼저 `pydantic`에서 `BaseModel`를 임포트해야 합니다.

{* ../../docs_src/body/tutorial001.py hl[4] *}

## 데이터 모델 생성하기

그 다음, `BaseModel`을 상속받는 클래스를 선언하여 데이터 모델을 정의합니다.

각 속성에는 표준 파이썬 타입(`int`, `str`, `bool` 등)을 사용하면 됩니다.

{* ../../docs_src/body/tutorial001.py hl[7:11] *}

쿼리 매개변수를 선언할 때와 같이, 데이터 모델의 각 속성이 기본 값을 가지고 있으면, 해당 속성은 필수가 아닙니다.
기본값을 가지고 있지 않는 모든 속성은 필수입니다.

예를 들어, 위의 모델은 다음과 같이 선언합니다.

```JSON
{
  "name": "Foo",
  "description": "선택적인 설명란",
  "price": 45.2,
  "tax": 3.5
}
```

`description`과 `tax`는 기본값이 존재하기 때문에, 아래와 같은 선언도 유효합니다.

```JSON
{
  "name": "Foo",
  "price": 45.2
}
```

## 매개변수로서 선언하기

여러분의 API에 요청 본문을 추가하기 위해서, 경로 매개변수와 쿼리 매개변수에서 선언했던 것과 같은 방식으로 선언하면 됩니다.

{* ../../docs_src/body/tutorial001.py hl[18] *}

`Annotated`와 함께 `Body()`를 넣어서 선언하면 됩니다.

## 데이터 검증

`/items`에 아래와 같은 본문을 담아 요청을 보내면

```JSON
{
  "name": "Foo",
  "description": "선택적인 설명란",
  "price": 45.2,
  "tax": "USA TAX"
}
```

`tax`가 `float`여야하지만 `str`로 잘못 선언되었습니다.
이 경우 다음과 같은 422 응답을 볼 수 있습니다.

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

경로 매개변수와 쿼리 매개변수에 대해서 동일하게 내부적인 Pydantic 기반의 데이터 검증 과정에서 오류가 발생하며, **Nexify**는 상세한 오류 메시지가 포함된 422 응답을 반환합니다.

## 문서화

모델의 JSON 스키마는 생성된 OpenAPI 스키마에 포함되며 Swagger UI에 포함됩니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/body/01-swagger-ui.png)
