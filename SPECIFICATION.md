# Open Reading Source Protocol 1.0

Status: **Early public draft**

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, and MAY in this
document are to be interpreted as described in RFC 2119 and RFC 8174.

## 1. Scope

ORSP defines discovery, search, book metadata, chapter catalogs, and chapter
content retrieval. Version 1.0 covers public HTTP(S) sources that do not require
user authentication.

## 2. Discovery

A source MUST expose a JSON discovery document at:

```text
/.well-known/open-reading-source.json
```

Clients MAY also accept the complete discovery-document URL from a user.

Required fields:

| Field | Requirement |
| --- | --- |
| `protocol` | MUST equal `open-reading-source` |
| `protocolVersion` | Semantic version; this specification uses `1.0` |
| `id` | Stable globally unique source identifier; reverse-domain form is recommended |
| `name` | Human-readable source name |
| `apiBaseUrl` | Absolute HTTP(S) API base URL |
| `capabilities` | MUST contain `search` |

Optional fields are `description`, `iconUrl`, `websiteUrl`, and `languages`.

Clients implementing version 1.x SHOULD accept discovery documents whose major
version is `1`. A source MUST NOT change its `id` when its host or display name
changes.

The discovery document is formally described by
[`schemas/discovery.schema.json`](schemas/discovery.schema.json).

## 3. Common requirements

- Requests and responses MUST use UTF-8.
- JSON responses MUST use `application/json`.
- Clients SHOULD send `X-Open-Reading-Protocol: 1.0`.
- IDs are stable opaque strings. Clients MUST NOT infer their structure.
- Timestamps MUST use ISO 8601.
- Production deployments SHOULD use HTTPS.
- Sources SHOULD return an `ETag` or suitable cache headers where practical.
- Clients MUST treat source HTML as untrusted input.

## 4. Search

```text
GET /v1/search?q={query}&page={page}&pageSize={pageSize}
```

`q` is required. `page` starts at 1. `pageSize` SHOULD be between 1 and 100.

Response:

```json
{
  "items": [
    {
      "id": "book-1001",
      "title": "Example Book",
      "author": "Example Author",
      "description": "A short description",
      "coverUrl": "https://books.example.org/covers/1001.jpg",
      "categories": ["Fiction"],
      "status": "completed",
      "latestChapter": "Chapter 30",
      "updatedAt": "2026-07-11T10:00:00Z"
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1,
  "hasMore": false
}
```

Book objects MUST include `id` and `title`. Other fields are optional.

## 5. Book details

```text
GET /v1/books/{bookId}
```

The response uses the same book object as search and MAY provide a longer
description or richer metadata.

## 6. Chapter catalog

```text
GET /v1/books/{bookId}/chapters
```

```json
{
  "items": [
    {
      "id": "chapter-1",
      "title": "Chapter One",
      "order": 1,
      "updatedAt": "2026-07-11T10:00:00Z"
    }
  ]
}
```

Chapter objects MUST contain `id`, `title`, and `order`. `order` is a
zero-or-positive integer used for deterministic display ordering.

## 7. Chapter content

```text
GET /v1/books/{bookId}/chapters/{chapterId}
```

```json
{
  "bookId": "book-1001",
  "chapterId": "chapter-1",
  "title": "Chapter One",
  "contentType": "text/plain",
  "content": "Chapter content"
}
```

`contentType` MUST be one of:

- `text/plain`
- `text/markdown`
- `text/html`

HTML MUST be a content fragment and MUST NOT contain executable scripts.
Clients SHOULD sanitize it before rendering.

## 8. Errors

Recommended status codes:

| Status | Meaning |
| --- | --- |
| `400` | Invalid request |
| `404` | Book, chapter, or route not found |
| `429` | Rate limited; `Retry-After` is recommended |
| `500` | Internal source error |
| `503` | Source temporarily unavailable |

Recommended error body:

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "The requested book does not exist"
  }
}
```

## 9. Security

Sources MUST validate query parameters and opaque IDs, SHOULD impose response
size and rate limits, and MUST NOT expose credentials, cookies, internal URLs,
or executable code. Web-facing sources are responsible for an appropriate CORS
policy.

## 10. Future work

The following features are intentionally outside version 1.0:

- authentication and paid-content authorization;
- incremental catalog synchronization;
- offline package/download manifests;
- source health and conformance endpoints;
- annotations, highlights, and reading-progress synchronization.
