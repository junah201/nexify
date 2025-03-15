# 미들웨어

미들웨어는 요청을 처리하기 전/후에 실행되는 함수 또는 클래스입니다. 요청을 가로채어 추가적인 로직을 수행하거나 응답을 변경할 수 있습니다.

## 사용자 지정 미들웨어 추가

### 데코레이터 기반 미들웨어 추가

```py
@app.middleware
def custom_middleware(route, event, context, call_next):
    response = call_next(event, context)
    response.headers["x-custom-header"] = "Custom Value"
    return response
```

### 함수 기반 미들웨어 추가

```py
def custom_middleware(route, event, context, call_next):
    response = call_next(event, context)
    response.headers["x-custom-header"] = "Custom Value"
    return response

app = Nexify(middlewares=[custom_middleware])
```

### 클래스 기반 미들웨어 추가

```py
from nexify.middleware import Middleware

class CustomMiddleware(Middleware):
    def __call__(self, route, event, context, call_next):
        response = call_next(event, context)
        response.headers["x-custom-header"] = "Custom Value"
        return response

app.add_middleware(CustomMiddleware())
```
