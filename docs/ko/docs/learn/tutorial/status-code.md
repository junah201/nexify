# 응답 상태 코드

`status_code` 매개변수를 이용하여 응답에 사용되는 HTTP 상태 코드를 선언할 수 있습니다.

{* ../../docs_src/status_code/tutorial001.py hl[6] *}

위와 같이 `status_code` 매개변수를 사용하여 응답 상태 코드를 설정할 수 있습니다.
이 값은 OpenAPI 문서에도 자동으로 반영됩니다.

![Swagger UI](https://nexify.junah.dev/img/learn/tutorial/status-code/01-swagger-ui.png)

## HTTP 상태 코드 (status code)란?

HTTP 상태 코드는 서버가 클라이언트의 요청을 처리한 결과를 나타내는 표준화된 숫자 코드입니다. 상태 코드는 크게 다섯 가지 범주로 나뉩니다.

- 1xx (정보 응답): 요청이 수신되었으며 처리 중임을 나타냅니다.
- 2xx (성공 응답): 요청이 성공적으로 처리되었음을 나타냅니다.
- 3xx (리디렉션 응답): 추가 작업이 필요하거나 다른 URL로 이동해야 함을 나타냅니다.
- 4xx (클라이언트 오류 응답): 클라이언트의 요청이 잘못되었거나 권한이 없음을 나타냅니다.
- 5xx (서버 오류 응답): 서버가 요청을 처리하는 중 오류가 발생했음을 나타냅니다.

## 주요 상태 코드 목록

### ✅ 성공 응답 (2xx)
- `200 OK`: 요청이 성공적으로 처리됨
- `201 Created`: 새 리소스가 성공적으로 생성됨
- `204 No Content`: 요청은 성공했지만 응답 본문이 없음

### 🔄 리디렉션 응답 (3xx)
- `301 Moved Permanently`: 리소스가 영구적으로 이동됨
- `302 Found`: 리소스가 임시로 이동됨
- `304 Not Modified`: 캐시된 리소스를 그대로 사용하도록 요청됨

### 🚫 클라이언트 오류 응답 (4xx)
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스를 찾을 수 없음
- `409 Conflict`: 충돌 발생 (예: 중복 데이터)

### ⚠️ 서버 오류 응답 (5xx)
- `500 Internal Server Error`: 서버 내부 오류 발생
- `502 Bad Gateway`: 게이트웨이 또는 프록시 서버 오류
- `503 Service Unavailable`: 서버가 일시적으로 사용 불가능

## Nexify.status

모든 HTTP 상태 코드를 기억할 필요 없이 `Nexify.status`에서 가져와 사용할 수 있습니다.

{* ../../docs_src/status_code/tutorial002.py hl[1,6] *}