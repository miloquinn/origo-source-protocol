# Open Reading Source Protocol

**English** · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) ·
[Specification](SPECIFICATION.md) · [OpenAPI](openapi.yaml)

Open Reading Source Protocol (ORSP) is an open HTTP contract for connecting
reading applications to independent book and serial-content providers.

A reader implements ORSP once. Source developers can then either:

- host a native ORSP service for original, public-domain, or licensed content;
- build an adapter in front of an existing service they are authorized to use.

The reader never needs source-specific scraping scripts, cookies, or executable
rules.

## Protocol at a glance

Every source publishes a discovery document:

```text
GET /.well-known/open-reading-source.json
```

It then implements four standard API operations:

```text
GET /v1/search?q={query}&page=1&pageSize=20
GET /v1/books/{bookId}
GET /v1/books/{bookId}/chapters
GET /v1/books/{bookId}/chapters/{chapterId}
```

Example discovery document:

```json
{
  "protocol": "open-reading-source",
  "protocolVersion": "1.0",
  "id": "org.example.public-books",
  "name": "Example Public Books",
  "description": "Public-domain books maintained by Example.org",
  "apiBaseUrl": "https://books.example.org/api/",
  "languages": ["en"],
  "capabilities": ["search", "detail", "catalog", "content"]
}
```

## Run the reference source

The repository includes a dependency-free Dart reference server with original
sample content:

```bash
dart run examples/dart_server.dart
```

The source will be available at `http://127.0.0.1:8787`. Add that URL to an
ORSP-compatible reader. Android emulators should use `http://10.0.2.2:8787`.

## Repository layout

```text
SPECIFICATION.md              Normative protocol specification
openapi.yaml                  OpenAPI 3.1 API description
schemas/discovery.schema.json Discovery-document JSON Schema
examples/dart_server.dart     Runnable reference source
```

## Status

Protocol version `1.0` is an early public draft. The discovery format and core
read path are implemented and tested in Open Reading, but feedback from source
developers is welcome before the specification is declared stable.

## Responsible use

ORSP is intended for original, public-domain, and properly licensed content.
Do not use it to bypass access controls, violate provider terms, or distribute
content without permission.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Protocol changes should include a clear
compatibility analysis and updated examples or schemas.

## License

[MIT](LICENSE)
