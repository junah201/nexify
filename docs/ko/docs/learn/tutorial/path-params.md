# 경로 매개변수 (Path)

파이썬의 문자열 format 문법을 이용해서 경로 "매개변수"를 선언할 수 있습니다.

{* ../../docs_src/path_params/tutorial001.py hl[8:9] *}

경로 매개변수 `item_id`의 값은 함수의 `item_id` 인자로 전달됩니다.

또한 Annotated 안에 있는 `Path()`는 이 함수 인자가 경로 매개변수임을 나타냅니다.

그리고 이 예제를 배포한 후, `/items/foo` 경로로 이동하면, 다음과 같은 응답을 볼 수 있습니다.

```JSON
{"item_id":"foo"}
```

## 다양한 타입의 경로 매개변수

경로 매개변수는 `str` 이외에도 `int`, `float`, `bool` 타입으로도 선언할 수 있습니다.

{* ../../docs_src/path_params/tutorial002.py hl[9] *}

위의 예시에서, `item_id`는 `int`로 선언되었습니다.

## 데이터 변환

이제 `/items/3` 경로로 이동하면, 다음과 같은 응답을 볼 수 있습니다.

```JSON
{"item_id":3}
```

/// check | 확인
함수가 받은 item_id의 값은 문자열 `"3"`이 아니라 Python `int` 타입인 `3`입니다.

이는 **Nexify**가 경로 매개변수에 선언된 타입(`int`)에 맞춰 자동으로 <abbr title="HTTP 요청에서 전달되는 문자열을 파이썬 데이터로 변환">"파싱"</abbr>하기 때문입니다. 즉, 문자열 `"3"`이 아닌 Python `int` 타입인 `3`으로 변환됩니다.
///


## 데이터 검증

하지만 `/items/foo` 경로로 이동하면, 다음과 같은 422 응답을 볼 수 있습니다.

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

422 상태 코드는 `"Unprocessable Entity"`를 의미합니다. 요청 자체는 유효하지만 제공된 데이터가 예상 형식과 맞지 않을 때 발생합니다.

예제에서 `/items/foo` 요청을 보낼 때 `"foo"`는 `int`로 변환될 수 없는 문자열이므로, 내부적인 Pydantic 기반의 데이터 검증 과정에서 오류가 발생하며, **Nexify**는 상세한 오류 메시지가 포함된 422 응답을 반환합니다.

또한 `int`가 아닌 `float` 값을 전달하는 경우에도 동일한 에러가 발생합니다. (`/items/3.14`)

/// check | 확인
즉, 경로 매개변수에 대해서 타입 선언을 하면 **Nexify**는 주어진 경로에 대해서 데이터 검증을 합니다.

오류에는 정확히 어느 데이터가 검증을 통과하지 못했는지 명시됩니다.

이는 API와 상호작용하는 코드를 제작하고, 디버깅하는데 매우 유용합니다.
///

### 데이터 검증의 이점

- **자동 검증**: 경로 매개변수의 타입을 선언하는 것만으로도 데이터 검증이 자동으로 수행됩니다.
- **명확한 오류 메시지**: 잘못된 입력이 잇을 경우, 어떤 데이터가 유효하지 않는지 상세한 오류 메시지가 제공됩니다. 이로 인해 코드 작성 및 디버깅이 쉬워집니다.

모든 데이터 검증은 내부적으로 <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a>에 의해 수행되므로 Pydantic의 다양한 기능을 그대로 활용할 수 있습니다.

이 중 몇 가지는 자습서의 <a href="https://nexify.junah.dev/ko/tutorial/path-params-with-validation" class="internal-link">경로 매개변수와 데이터 검증</a>에서 확인할 수 있습니다.

## 문서화

그리고 `/docs`경로로 이동하면, 다음과 같은 Swagger UI가 제공됩니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/path-params/01-swagger-ui.png)

/// check | 확인
**Nexify**는 단순히 파이썬 타입 힌트를 추가하는 것만으로 이에 맞는 API 문서를 자동 생성하기 때문에, 경로 매개변수가 `int` 타입으로 명시된 것을 확인할 수 있습니다.
///

## 경로 적용 순서

예를 들어, 모든 아이템을 가져오는 `items/all`과 특정 아이템을 조회하는 `items/{item_id}`를 동시에 정의할 수 있습니다.

{* ../../docs_src/path_params/tutorial003.py hl[8,13] *}

**Nexify**에서는 경로 선언 순서와 상관 없이 고유한 함수명을 가지기만하면, 자동으로 올바른 API 경로가 매핑됩니다.

## 여러 경로 매개변수

여러 개의 경로 매개변수를 포함해서 선언할 수도 있습니다. 예를 들어,  `item_id`와 `user_id`를 동시에 포함하는 경로를 만들 수 있습니다.

{* ../../docs_src/path_params/tutorial004.py hl[8:9] *}

위 예제에서 `item_id`와 `user_id`는 각각 `int`와 `str` 타입으로 선언되었습니다.

## 요약

**Nexify**를 사용하면 간단한 Python 타입 힌트만으로 강력한 API를 구축할 수 있습니다.

- 에디터 지원: 오류 검사, 자동완성 등
- 데이터 <abbr title="HTTP 요청에서 전달되는 문자열을 파이썬 데이터로 변환">"파싱"</abbr>
- 데이터 검증
- API 문서 자동 생성

추가적인 데이터 검증과 고급 기능은 <a href="https://nexify.junah.dev/ko/tutorial/path-params-with-validation" class="internal-link">경로 매개변수와 데이터 검증</a>에서 확인할 수 있습니다.