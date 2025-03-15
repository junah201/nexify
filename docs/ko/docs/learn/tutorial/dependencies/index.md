# 의존성 주입

**Nexify**는 강력하면서도 직관적인 의존성 주입(Dependency Injection) 시스템을 제공합니다.

이 시스템은 사용하기 쉽게 설계되었으며, 개발자가 **Nexify**를 다른 컴포넌트와 손쉽게 통합할 수 있도록 도와줍니다.

## "의존성 주입"은 무엇입니까?

**의존성 주입**(Dependency Injection, DI)은 여러분의 코드(핸들러)가 실행되기 위해 필요한 "의존성"을 선언하는 방법입니다.

이후 **Nexify**는 필요한 모든 작업을 처리하여 해당 의존성을 "주입"합니다.

이 시스템은 다음과 같은 경우에 특히 유용합니다:

- 공통 로직을 여러 곳에서 재사용해야 할 때 (중복 코드 방지)
- 데이터베이스 연결을 공유해야 할 때
- 인증, 보안, 권한 관리 등의 기능을 강제해야 할 때
- 기타 다양한 상황에서 모듈화된 코드 작성을 원할 때

## 의존성 사용 예제

의존성 주입이 어떻게 작동하는지 이해하기 위해 간단한 예제를 살펴보겠습니다.

### `Depends` import

먼저 `Depends`를 import합니다.

{* ../../docs_src/dependencies/tutorial001.py hl[3] *}

### 의존성 함수 정의하기

{* ../../docs_src/dependencies/tutorial001.py hl[8:13] *}

이 `common_parameters` 함수는 다음과 같은 쿼리 매개변수를 기대합니다:

- 선택적 쿼리 매개변수 `q`.
- 선택적 쿼리 매개변수 `skip` (기본값: `0`)
- 선택적 쿼리 매개변수 `limit` (기본값: `100`)

그리고 이 값들을 포함한 `dict`를 반환합니다.

### 의존성 주입하기

{* ../../docs_src/dependencies/tutorial001.py hl[17,22] *}

**Nexify**의 내부 동작 과정:

1. 요청이 들어오면, **Nexify**는 먼저 `common_parameters` 함수를 실행합니다.
2. 그 결과 값을 `commons` 매개변수에 할당합니다.
3. `read_items` 핸들러는 `commons`를 사용하여 응답을 생성합니다.

이렇게 하면 불필요한 코드 반복을 방지하고, 코드 유지보수가 쉬워집니다.

### `Annotated`인 코드 중복 최소화하기

만약 같은 의존성을 여러 핸들러에서 사용해야 한다면, 타입 정의를 변수에 할당하여 코드 중복을 줄일 수 있습니다.

{* ../../docs_src/dependencies/tutorial002.py hl[16,20,25] *}

### 문서화

**Nexify**의 의존성 주입 시스템은 자동으로 OpenAPI 문서에도 반영됩니다.
즉, 의존성에서 사용하는 매개변수들이 API 문서에도 그대로 표시됩니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/dependencies/index.md/01-swagger-ui.png)
