# 첫걸음

먼저 프로젝트를 생성해봅시다.

<div class="termy">

```console
$ nexify init
Enter the project name: myapp
🎉 Project myapp created at 'C:\Users\junah\Desktop\myapp'
$ cd myapp
```

</div>

`nexify deploy` 명령어를 실행하면 `main.py` 및 `nexify.json` 설정 파일이 생성됩니다.

{* ../../docs_src/first_steps/tutorial001.py *}

이를 생성된 `main.py`에 붙여넣기 합니다.

/// check
AWS CLI를 설치하고, `aws configure` 명령어를 통해서 자격 증명을 등록했다는 것을 전제로 합니다. 만약 이 작업을 하지 않은 분은 <a href="https://nexify.junah.dev/ko/learn/aws-cli">AWS CLI</a> 문서를 참고해서 이 작업을 먼저 진행해주세요.
///

<div class="termy">

```console
// 배포 명령어를 입력해서 배포를 진행해주세요.
$ nexify deploy
// 곧 아래와 같은 출력을 얻게 됩니다.
✔ App imported successfully!
✔ Config loaded successfully!
✔ App analyzed successfully!
✔ Requirements installed successfully!
✔ Lambda functions packaged successfully!
✔ Basic stack created successfully!
✔ Template created successfully!
✔ Stack updated successfully!

🎉 Deployment successful!

Endpoints:
    - GET   https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/


API Docs:
    - openapi    https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/openapi.json
    - Swagger    https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs
    - ReDoc      https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc


Functions:
    - root
```

</div>

## 확인하기

브라우저로 다음 URL을 열어 API 응답을 확인해보세요.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///

이러한 응답을 확인할 수 있습니다:
```JSON
{"message": "Hello World"}
```

## Swagger UI

이제 브라우저로 다음 URL을 열어 Swagger UI 문서를 확인해보세요.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///

Swagger UI를 기반으로 자동 생성된 API 문서를 확인할 수 있습니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/first-steps/01-swagger-ui-simple.png)

## ReDoc

이번에는 브라우저로 다음 URL을 열어 ReDoc 문서를 확인해보세요.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///

ReDoc를 기반으로 자동 생성된 API 문서를 확인할 수 있습니다.

![ReDoc](https://nexify.junah.dev/img/learn/tutorial/first-steps/02-redoc-simple.png)

## OpenAPI

**Nexify**는 자동으로 정의된 모든 API를 OpenAPI 표준에 따라 Schema(스키마)를 생성합니다.

#### "Schema" (스키마)

"Schema"는 무언가의 정의 또는 설명입니다. 이를 구현하는 코드가 아니라 이해를 돕기 위한 추상적인 설명입니다.

#### API "Schema"

OpenAPI에서 어떻게 API의 schema를 정의하는지를 정하는 사양입니다.

API Schema에는 API 경로(Path), 사용 가능한 매개 변수 등이 포함됩니다.

#### Data "Schema"

JSON 데이터 속성과 해당 속성이 가지고 있는 데이터 유형 등을 의미합니다.

#### OpenAPI Schema

OpenAPI 스키마는 API에서 사용되는 구조 및 데이터 유형의 공식 정의입니다. 이는 입력 및 출력 데이터 형식을 설명하며, API 작업에 관련된 매개변수, 요청 본문, 응답 및 객체를 포함합니다.

#### `openapi.json` 확인하기

Nexify는 자동으로 API에 대한 여러 정보와 함께 JSON schema를 생성합니다.

가공되지 않는 OpenAPI schema가 어떻게 생겼는지 궁금하다면, 여기에서 직접 확인할 수 있습니다.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/openapi.json
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///

```JSON
{
  "openapi": "3.1.0",
  "info": {
    "title": "Nexify API",
    "version": "0.1.0",
    "description": ""
  },
  "paths": {
    "/": {
      "get": {
        "summary": "Root",
        "operationId": "root__get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
...
```


#### OpenAPI의 장점

Nexify는 API의 배포와 함께 OpenAPI Spec를 매번 생성함으로써 신뢰도 높은 OpenAPI 문서 제공합니다.
이러한 OpenAPI 문서는 아래와 같은 장점들이 있습니다.

- 개발자들이 API의 엔드포인트, 요청/응답의 스펙을 쉽게 확인할 수 있습니다.
- 팀원 혹은 외부 개발자에게 API 명세를 명확하게 공유할 수 있습니다.
- API와 통신하는 클라이언트 (프론트엔드, 모바일, IoT 애플리케이션 등)를 위해 코드를 자동으로 생성할 수도 있습니다.

## 예제 코드의 단계별 분석

### Step 1: import `Nexify`

{* ../../docs_src/first_steps/tutorial001.py hl[1] *}

`Nexify`는 AWS Lambda Python 런타임에서 API를 구축하기 위한 거의 모든 기능을 제공하는 파이썬 클래스입니다.

/// info | API Reference
[Nexify class](https://nexify.junah.dev/reference/nexify)에서 `Nexify` 클래스의 reference를 확인할 수 있습니다.
///

### Step 2: `Nexify` 인스턴스 생성

{* ../../docs_src/first_steps/tutorial001.py hl[3] *}

여기에서 `app` 변수는 `Nexify` 클래스의 "인스턴스"입니다.

이 인스턴스는 API를 생성하는 모든 상호작용의 중심 역할을 하며, 여러분의 애플리케이션에서 주요한 진입점이 됩니다.

### Step 3: API Route 정의

#### Path (경로)

여기서 Path는 URL에서 첫 번째 `/`에서 시작하는 URL의 뒷부분을 의미합니다.

예를 들어 아래와 같은 URL에서

```
https://example.com/items/foo
```

Path는 다음과 같습니다.

```
/items/foo
```

/// info
"Path"는 일반적으로 "Endpoint (엔드포인트)" 혹은 "Route (라우트)"라고도 불립니다.
///

API를 설계할 때 "Path"는 "Domain (관심사)"와 "Resource (리소스)"를 분리하기 위한 주된 방법입니다.

#### Method (메서드)

여기서 "Method"는 HTTP Method를 의미합니다.

다음 중 하나이며:

- `GET`
- `POST`
- `PUT`
- `DELTE`

흔히 사용되지 않는 Method들도 있습니다.

- `OPTIONS`
- `HEAD`
- `PATCH`
- `TRACE`

우리가 사용할 HTTP 프로토콜에서는 이러한 "Method"를 사용하여 각 경로와 통신할 수 있습니다.

---

API를 설계할 때 우리는 일반적으로 특정 행동을 수행하기 위해서 특정 HTTP Method를 사용합니다. 이는 일종의 약속이며, 각 메서드는 특정한 용도를 가지고 있습니다. 예를 들어:

- `GET` : 데이터를 조회하기 위해
- `POST` : 데이터를 생성하기 위해
- `PUT` : 데이터를 수정하기 위해
- `DELTE` : 데이터를 삭제하기 위해

이 외에도 `OPTIONS`, `HEAD`, `PATCH`, `TRACE`와 같은 Method들은 덜 사용되지만, 특수한 용도나 서버 상태 확인 등에 사용될 수 있습니다.

이처럼 API 설계에서 `Path`와 `Method`는 서로 결합되어 특정 작업을 지정하고, 클라이언트가 필요로 하는 데이터를 정확하게 요청하고 받을 수 있게 합니다.

#### 데코레이터 정의

{* ../../docs_src/first_steps/tutorial001.py hl[6] *}

`@app.get("/")`는 Nexify에게 `/` 경로로 `GET` 요청이 오면 바로 아래에 있는 함수가 이 요청을 처리한다는 것을 알려줍니다.

- Path: `/`
- Method: `GET`

/// info | 데코레이터터
이 `@something` 문법은 파이썬에서 "데코레이터"라고 부릅니다.

이 데코레이터를 함수 맨 위에 모자처럼 놓고, 데코레이터는 아래에 있는 함수를 받아 그것으로부터 무언가를 합니다.

이 경우 Nexify에게 아래 함수가 Path `/`의 `GET` Method에 해당한다고 알려줍니다.
///

물론 아래와 같은 method들도 사용할 수 있습니다.

- `@app.post()`
- `@app.put()`
- `@app.delete()`
- `@app.options()`
- `@app.head()`
- `@app.patch()`

#### 함수 정의

{* ../../docs_src/first_steps/tutorial001.py hl[7] *}

이것은 일반적인 파이썬 함수로, URL `/`에 대한 `GET` Method 요청을 받을 때마다 `Nexify`에 의해서 호출됩니다.

#### 함수 리턴값

{* ../../docs_src/first_steps/tutorial001.py hl[8] *}

`dict`, `list`, 혹은 단일값을 가진 `str`, `int` 등을 반환할 수 있습니다.

Pydantic 모델을 반환할 수도 있습니다. (이것에 대해서는 나중에 더 자세히 살펴봅시다.)
