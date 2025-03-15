# 응답 모델

리턴 타입을 이용해서 응답 모델을 지정할 수 있습니다.

{* ../../docs_src/response_model/tutorial001.py hl[20] *}

**Nexify**는 이 리턴 타입을 이용해서 다음과 같은 작업을 수행합니다:

- 출력 데이터를 해당 리턴 타입으로 변환
- 데이터 검증
- OpenAPI 문서에 활용

여기서 가장 중요한 부분은 해당 모델의 출력 데이터를 제한하는 것입니다. 이는 보안적인 측면에서도 중요한 역할을 합니다.

## 동일한 입력 데이터 반환

우리는 여기서 비밀번호를 포함하는 `UserIn` 모델을 선언합니다.

{* ../../docs_src/response_model/tutorial002.py hl[9,13] *}

이 경우 비밀번호가 포함된 응답을 사용자에게 반환하게 됩니다. 이는 보안상 바람직하지 않은 방식입니다.

## 출력 모델 추가

대신 비밀번호가 포함되지 않는 UserOut 모델을 추가로 선언하고 이를 리턴 타입으로 지정할 수 있습니다.

{* ../../docs_src/response_model/tutorial003.py hl[9,13,16,23] *}

이 경우, 비밀번호를 포함하는 동일한 사용자 입력을 반환하더라도, UserOut을 리턴 타입으로 선언했기 때문에 비밀번호가 포함되지 않습니다. 이를 통해 불필요한 민감 정보 노출을 방지할 수 있습니다.

## 문서화

Swagger UI를 보면 입력 모델과 출력 모델이 각자의 JSON 스키마를 가지고 있음을 확인할 수 있습니다.

![Swagger UI 01](https://nexify.junah.dev/img/learn/tutorial/response-model/01-swagger-ui.png)

이 두 모델 모두 `/user` 경로에 활용됩니다.

![Swagger UI 02](https://nexify.junah.dev/img/learn/tutorial/response-model/02-swagger-ui.png)
