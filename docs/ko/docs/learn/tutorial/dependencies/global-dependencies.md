# 전역 의존성

일부 경우에는 애플리케이션 전역에 의존성을 추가해야 할 수도 있습니다.

<a href="https://nexify.junah.dev/ko/tutorial/dependencies-in-decorators" class="internal-link">데코레이터 내에서의 의존성 사용</a>와 유사한 방법으로 **Nexify** 애플리케이션에 전역 의존성을 추가할 수 있습니다.

이렇게 설정하면 애플리케이션 내의 모든 핸들러에서 해당 의존성이 실행됩니다.

{* ../../docs_src/dependencies/tutorial006.py hl[17] *}

위 코드에서 `verify_token`과 `verify_key` 의존성은 모든 핸들러에서 실행됩니다.

전역 의존성을 활용하면 개별 핸들러에서 반복적으로 같은 의존성을 선언할 필요 없이, 애플리케이션 전체에 일관된 검증 및 로직을 적용할 수 있습니다.

<a href="https://nexify.junah.dev/ko/tutorial/dependencies-in-decorators" class="internal-link">데코레이터 내에서의 의존성 사용</a>에 사용된 모든 개념은 여전히 적용되지만 여기에서는 애플리케이션에 있는 모든 핸들러에 적용됩니다.