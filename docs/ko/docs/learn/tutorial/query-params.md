# 쿼리 매개변수 (Query)

`Query()`와 함께 함수 매개변수를 선언하면 "쿼리" 매개변수를 선언할 수 있습니다.

{* ../../docs_src/query_params/tutorial001.py hl[12] *}

쿼리 파라미터 (Query Parameter)는 URL 뒤에 물음표(`?`)와 함께 붙은 키-값(Key-Value) 쌍입니다. 여러 개의 쿼리 파라미터를 전달하려면 파라미터 사이에 앰퍼샌드(`&`)를 추가해서 하나의 문자열(`string`)으로 전달할 수 있습니다.

예를 들어, 아래의 URL에서

```
/items?skip=0&limit=10
```

쿼리 매개변수는:

- skip: 값 `0`을 가집니다.
- limit: 값 `10`을 가집니다.

이 값은 URL의 일부이므로 당연히 문자열입니다.

하지만 우리는 파이썬 타입과 같이 선언 했기 때문에 (위 예시에서는 `int`), 해당 타입으로 변환 및 검증됩니다.

경로 매개변수에 적용된 동일한 기능들이 쿼리 매개변수에도 적용됩니다:

- 에디터 지원
- 데이터 파싱
- 데이터 검증
- 자동 문서화

## 기본값

쿼리 매개변수는 경로에서 고정된 부분이 아니기 때문에, 선택적일 수도 있고 기본값을 가질 수도 있습니다.

/// info
쿼리 매개변수와 다르게 경로 매개변수는 선택적일 수도, 기본값을 가질 수도 없습니다.
///

위의 예시에서 `skip`은 `0`의 기본값을 가지고 있고, `limit`은 `10`의 기본값을 갖고 있습니다.

따라서 `/items`로 이동하는 것은 `/items?skip=0&limit=10`으로 이동하는 것과 같습니다.

하지만 만약 `/items?skip=20`으로 이동하게 될 경우

- `skip=20`: URL에서 직접 지정했기 때문에 `20`의 값을 가집니다.
- `limit=10`: 기본값이 `10`이기 때문에 `10`의 값을 가집니다.

## 다른 기본값 선언 방식

`Annotated`안에 있는 `Query()`에 `default` 매개변수를 넣어주어 기본값을 넣어줄 수도 있습니다.

{* ../../docs_src/query_params/tutorial002.py hl[12] *}

위 예시에서 동일하게 `skip`은 `0`의 기본값을 가지고 있고, `limit`은 `10`의 기본값을 갖고 있습니다.

이러한 방식으로 기본값을 선언하게 되면, 파이썬에서의 기본값이 없는 매개변수는 항상 기본값이 있는 매개변수 앞에 와야하는 제약을 회피할 수 있습니다. 이것은 일부 상황에서 유용할 수 있습니다.

---

혹은 `Annotated`안에 있는 `Query()`에 `default_factory` 매개변수를 넣어주어 기본값을 넣어줄 수도 있습니다.

{* ../../docs_src/query_params/tutorial003.py hl[16:17] *}

`default_factory`는 여러 상황에서 **매우** 유용할 수 있습니다.

- 매 요청마다 동적인 값이 필요할 때: 위 예시처럼 `datetime.now()`가 호출할 때마다 다른 값이 반환되는 경우
- Mutable한 객체를 기본값으로 사용할 때: `list`나 `dict`를 기본값으로 설정하고 싶을 때, `default_factory=list` 또는 `default_factory=dict`를 사용하면 `None` 체크 없이 바로 활용 가능합니다.
- 계산된 기본값을 제공할 때: 특정 로직을 통해 기본값을 설정해야 하는 경우, 함수로 감싸서 `default_factory`로 전달하면 클린한 코드 유지 가능합니다.

## 데이터 검증

{* ../../docs_src/query_params/tutorial001.py hl[12] *}

하지만 `/items?skip=foo` 경로로 이동하면, 다음과 같은 422 응답을 볼 수 있습니다.

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

경로 매개변수 자습서의 내용과 동일하게, `"foo"`는 `int`로 변환될 수 없는 문자열이므로, 내부적인 Pydantic 기반의 데이터 검증 과정에서 오류가 발생하며, **Nexify**는 상세한 오류 메시지가 포함된 422 응답을 반환합니다.

## 문서화

그리고 `/docs`경로로 이동하면, 다음과 같은 Swagger UI가 제공됩니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/query-params/01-swagger-ui.png)

/// check | 확인
**Nexify**는 단순히 파이썬 타입 힌트를 추가하는 것만으로 이에 맞는 API 문서를 자동 생성하기 때문에, 쿼리 매개변수가 `int` 타입으로 명시된 것을 확인할 수 있습니다. 기본값 또한 `0`과 `10`으로 명시된 것을 확인할 수 있습니다.
///

## 필수 쿼리 매개변수

기본값을 가지는 쿼리 매개변수는 모두 **선택적**입니다. 하지만 쿼리 매개변수를 필수로 만들려면 단순히 기본값을 선언하지 않으면 됩니다.

{* ../../docs_src/query_params/tutorial004.py hl[12] *}

`/items` 경로로 이동하면, 다음과 같은 422 응답을 볼 수 있습니다.

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

기본값이 없기 때문에 필수 쿼리 매개변수인 `skip`과 `limit`가 누락되었다는 것을 알려주는 응답입니다.

또한 문서에서도 `required`라는 것을 통해서 해당 쿼리 매개변수가 필수라는 것을 알려줍니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/query-params/02-swagger-ui.png)