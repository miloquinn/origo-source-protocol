# Origo Source Protocol

[English](README.md) · [简体中文](README.zh-CN.md) ·
[繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · **한국어** ·
[Español](README.es.md) · [명세](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

Origo Source Protocol(ORSP)은 독서 앱과 독립 콘텐츠 서비스를 연결하는 공개 HTTP
프로토콜입니다. 검색, 도서 정보, 목차 및 본문을 하나의 공통 인터페이스로 제공합니다.

리더 앱은 ORSP를 한 번만 구현하면 모든 호환 도서 소스에 연결할 수 있습니다. 소스 개발자는
창작물, 퍼블릭 도메인 또는 정식으로 사용 허가를 받은 콘텐츠를 위한 서비스를 직접 운영하거나,
사용 권한이 있는 기존 서비스 앞에 ORSP 어댑터를 구축할 수 있습니다.

## 프로토콜 개요

각 소스는 디스커버리 문서를 공개해야 합니다.

```text
GET /.well-known/origo-source.json
```

그리고 네 개의 핵심 엔드포인트를 구현합니다.

```text
GET {apiBaseUrl}v1/search?q={query}&page=1&pageSize=20
GET {apiBaseUrl}v1/books/{bookId}
GET {apiBaseUrl}v1/books/{bookId}/chapters?page=1&pageSize=100
GET {apiBaseUrl}v1/books/{bookId}/chapters/{chapterId}
```

버전 1.6는 선택적 탐색, 카테고리, 둘러보기 및 다중 순위 엔드포인트도 정의합니다.

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
GET {apiBaseUrl}v1/rankings
GET {apiBaseUrl}v1/rankings/{rankingId}?page=1&pageSize=20
```

필드와 오류 처리에 대한 자세한 내용은 [프로토콜 명세](SPECIFICATION.md)와
[OpenAPI 3.1 문서](openapi.yaml)를 참고하세요.

## 테스트 소스 실행

이 저장소에는 외부 패키지에 의존하지 않는 Dart 참조 서버가 포함되어 있습니다. 예제 도서와
본문은 모두 테스트를 위한 자체 제작 콘텐츠입니다.

```bash
dart run examples/dart_server.dart
```

PC에서는 `http://127.0.0.1:8787`, Android 에뮬레이터에서는
`http://10.0.2.2:8787`을 사용하세요.

## 자체 도서 소스 개발

1. 소스 ID, 버전, API URL과 기능을 선언하는 디스커버리 문서를 제공합니다.
2. 검색, 상세 정보, 목차와 본문 엔드포인트를 구현합니다.
3. 도서와 장에 안정적인 불투명 ID를 사용합니다.
4. UTF-8 JSON과 올바른 HTTP 상태 코드를 반환합니다.
5. [JSON Schema](schemas/discovery.schema.json)와 [OpenAPI](openapi.yaml)로 출력을 검증합니다.
6. 실제 HTTP 요청을 사용해 호환성을 테스트합니다.

## 상태 및 책임 있는 사용

프로토콜 `1.6`는 후보 초안입니다. 핵심 읽기 흐름은 검증되었지만 안정 버전 발표 전까지
인증, 동기화, 페이지 처리 및 콘텐츠 형식에 대한 의견을 환영합니다.

ORSP는 창작물, 퍼블릭 도메인 및 정식 허가를 받은 콘텐츠를 위한 것입니다. 접근 제어를
우회하거나 서비스 약관을 위반하거나 무단 콘텐츠를 배포하는 데 사용하지 마세요.

기여 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요. 이 저장소는
[MIT](LICENSE) 라이선스를 사용합니다.

[ORSP 1.6 reading profiles](OEP-0006-media-reading.md) · [Upgrade guide](docs/source-upgrade-guide.zh-CN.md) · [Reference validation](scripts/validate_reading_profiles.py)
