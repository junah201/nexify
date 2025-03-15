# 에러 헨들링

**Nexify**는 에러를 처리하기 위한 에러 핸들러를 제공합니다. 에러 핸들러를 사용하면 특정 에러가 발생했을 때 일관된 응답을 반환하고, 에러를 적절하게 로깅하거나 변환할 수 있습니다.

에러 핸들러는 특정 에러 유형을 감지하고, 해당 에러가 발생했을 때 사용자 정의 응답을 생성하는 역할을 합니다. **Nexify**에서는 사용자 지정 에러 핸들러를 추가할 수 있으며, 기본적으로 제공되는 에러 핸들러도 있습니다.

## 사용자 지정 에러 핸들러 추가하기

**Nexify**에서 사용지 지정 에러 핸들러를 추가하는 방법은 총 세 가지 있습니다.

### 데코레이터 사용

데코레이터 방식으로 에러 핸들러를 등록할 수도 있습니다.

{* ../../docs_src/exception_handling/tutorial001.py hl[12] *}

### `add_exception_handler` 메서드 사용

`add_exception_handler` 메서드를 사용하여 특정 예외에 대한 핸들러를 추가할 수 있습니다.

{* ../../docs_src/exception_handling/tutorial002.py hl[16] *}

### 클래스 기반 예외 핸들러 사용

클래스 기반 예외 핸들러를 정의할 수 있습니다.

{* ../../docs_src/exception_handling/tutorial003.py hl[11:13,16] *}

## 내장 에러 핸들러

**Nexify**는 기본적으로 세 가지 예외 핸들러를 내장하고 있습니다.

### HTTPException

HTTPException이 발생하면 해당 예외의 status_code와 detail을 포함한 JSON 응답을 반환합니다.

```py
def http_exception_handler(event: EventType, _context: ContextType, exc: HTTPException) -> Response:
    headers = getattr(exc, "headers", None)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=headers)
```

### RequestValidationError

요청 데이터가 유효성 검사를 통과하지 못하면 `422 Unprocessable Entity` 상태 코드와 함께 유효성 검사 오류 정보를 반환합니다.

```py
def request_validation_exception_handler(
    event: EventType, _context: ContextType, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors)},
    )
```

### ResponseValidationError

API 응답 데이터가 유효성 검사를 통과하지 못하면 `500 Internal Server Error` 상태 코드와 함께 기본 오류 메시지를 반환합니다.

```py
def response_validation_exception_handler(
    event: EventType, _context: ContextType, exc: ResponseValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
```
