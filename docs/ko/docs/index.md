---

**공식 문서**: <a href="https://nexify.junah.dev" target="_blank">https://nexify.junah.dev</a>

**소스 코드**: <a href="https://github.com/junah201/nexify" target="_blank">https://github.com/junah201/nexify</a>

---

**Nexify**는 Python 표준 타입 힌트를 기반으로 AWS Lambda Python 런타임에서 API를 구축하는 경량 웹 프레임워크입니다.

주요 기능은 다음과 같습니다.

- 🚀 **자동 파싱**: AWS Lambda의 Event 및 Context 객체를 자동으로 파싱합니다.
- 🔍 **데이터 검증**: Pydantic을 활용한 입력 및 응답 데이터 검증을 제공합니다.
- 📜 **OpenAPI 문서화**: Swagger UI 및 ReDoc를 통한 API 문서를 자동 생성합니다.
- ☁️ **배포 자동화**: 단순한 명령어로 AWS Lambda를 포함한 AWS 인프라를 손쉽게 배포할 수 있습니다.

## 요구사항

Nexify는 다음과 같은 라이브러리를 필요로 합니다.

- <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a> 데이터 유효성 검사 및 OpenAPI 문서 제작을 위해 사용됩니다.
- <a href="https://boto3.amazonaws.com/v1/documentation/api/latest/index.html" class="external-link" target="_blank">Boto3</a> AWS 배포에 사용됩니다. (로컬 개발 환경에서만 필요하며, 프로덕션 환경에서는 불필요합니다.)

## 설치

먼저 가상환경을 설정한 후, Nexify를 설치하세요.

<div class="termy">

```console
$ pip install "nexify[cli]"

---> 100%
```

</div>

/// info
일부 터미널 환경에서는 `"nexify[cli]"`처럼 따옴표를 사용해야 올바르게 설치됩니다.
///

## 사용법

### 프로젝트 생성

<div class="termy">

```console
$ nexify init
Enter the project name: myapp
🎉 Project myapp created at 'C:\Users\junah\Desktop\myapp'
$ cd myapp
```

</div>

이 명령어를 실행하면 `main.py` 및 `nexify.json` 설정 파일이 생성됩니다.

- `main.py` 예제 코드

```py
from typing import Annotated

from nexify import Body, Nexify, Path, Query, status
from pydantic import BaseModel, Field

app = Nexify(title="My Nexify API", version="0.1.0")


class Item(BaseModel):
    id: str
    name: str
    price: Annotated[int, Field(ge=0)]


@app.get("/items")
def read_items(limit: Annotated[int, Query(default=10)]) -> list[Item]:
    return [Item(id=f"{i + 1}", name=f"Item {i}", price=i * 10) for i in range(limit)]


@app.post("/items", status_code=status.HTTP_204_NO_CONTENT)
def create_item(item: Annotated[Item, Body()]): ...


@app.get("/items/{item_id}")
def read_item(item_id: Annotated[str, Path(min_length=2, max_length=8)]) -> Item:
    return Item(id=item_id, name="Foo", price=42)
```

- `nexify.json` 설정 예제

```json
{
  "service": "myapp",
  "provider": {
    "name": "aws",
    "runtime": "python3.10",
    "region": "ap-northeast-2",
    "profile": "default",
    "logRetentionInDays": 14,
    "architecture": "x86_64",
    "memorySize": 128,
    "timeout": 10,
    "stage": "prod",
    "environment": { "YOUR_CUSTOM_ENV": "${env:YOUR_CUSTOM_ENV}" },
    "iamRoleStatements": [
      { "Effect": "Allow", "Action": ["s3:*"], "Resource": "*" }
    ]
  },
  "package": {
    "include": ["main.py"],
    "exclude": [".venv/**", ".git/**", ".gitignore"],
    "pipCmdExtraArgs": [""]
  },
  "resources": {
    "Resources": {
      "APIGatewayRestAPI": {
        "Type": "AWS::ApiGateway::RestApi",
        "Properties": {
          "Name": "myapp-API",
          "EndpointConfiguration": { "Types": ["EDGE"] },
          "Policy": "",
          "Description": "API for myapp"
        }
      }
    }
  }
}
```

### 배포하기


<div class="termy">

```console
$ nexify deploy
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
    - GET   https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items
    - POST  https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items
    - GET   https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items/{item_id}


API Docs:
    - openapi    https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/openapi.json
    - Swagger    https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs
    - ReDoc      https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc


Functions:
    - read_items
    - create_item
    - read_item
```

</div>

배포가 완료되면 API 엔드포인트가 생성됩니다.

/// info
첫 배포에는 약 1분이 소요될 수 있지만, 이후 업데이트 배포는 30초 이내로 완료됩니다.
///


### API 확인하기

브라우저로 다음 URL을 열어 API 응답을 확인해보세요.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/items/12
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///


응답 예시

```json
{"id":"12","name":"Foo","price":42}
```

---

벌써 API를 만들었습니다.

- `/items`와 `/items/{item_id}`에서 HTTP 요청을 받을 수 있습니다.
- `items`에서는 `GET`과 `POST` 요청을 받고, `/items/{item_id}`는 `GET` 요청을 받습니다.
- `/items`에서는 `GET` 요청을 보냈을 때, 기본값 `10`을 가지는 `int`형 쿼리 매개변수를 가지고 있습니다.
- `/items/{item_id}`에서는 최소 2글자에서 8글자 이내의 `str`형 경로 매개변수 `item_id`를 가지고 있습니다.

Nexify는 내부적으로 <a href="https://docs.pydantic.dev" class="external-link" target="_blank">Pydantic</a> 이용해서 입력값과 응답값이 올바른지 검증합니다.

### Swagger UI

브라우저로 다음 URL을 열어 Swagger UI 문서를 확인해보세요.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/docs
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///

Swagger UI를 기반으로 자동 생성된 API 문서를 확인할 수 있습니다.

![Swagger UI](https://nexify.junah.dev/img/index/index-01-swagger-ui-simple.png)

### ReDoc

이번에는 다음 URL을 열어 ReDoc 문서를 확인해보세요.

```
https://apigatewayid.execute-api.ap-northeast-2.amazonaws.com/prod/redoc
```

/// check
URL은 `nexify deploy` 명령어를 실행 후 결과값으로 나온 URL을 사용하여야 합니다.
///

ReDoc를 기반으로 자동 생성된 API 문서를 확인할 수 있습니다.

![ReDoc](https://nexify.junah.dev/img/index/index-02-redoc-simple.png)

### 요약

`Nexify`를 사용하면 표준 Python 타입 힌트만으로 <a href="https://aws.amazon.com/ko/pm/lambda" target="_blank">AWS Lambda</a> 기반의 API를 쉽게 개발할 수 있습니다.

- 🔍 **데이터 검증**: `Pydantic`을 활용하여 입력 및 응답 값을 검증합니다.
    - 데이터가 유효하지 않을 때 자동으로 생성하는 명확한 에러
    - 중첩된 JSON 객체에 대한 유효성 검사
- 📦 **자동 파싱**: `Event` 객체에서 `body`, `pathParameters`, `queryStringParameters` 등을 자동으로 추출합니다.
- 🔄 **응답 변환**: 파이썬 기본 타입인 `str`, `int`, `float`, `bool`, `list` 등 뿐만 아니라 `datetime`, `UUID`, `dataclass`를 포함한 다양한 객체를 자동 변환합니다.
- 📜 **OpenAPI 문서화**: Swagger UI 및 ReDoc 지원
- ☁️ **배포 자동화**: `nexify deploy` 단 한 줄의 명령어로 AWS Lambda를 포함한 AWS 인프라를 손쉽게 배포할 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스 조약에 따라 라이선스가 부여됩니다.
