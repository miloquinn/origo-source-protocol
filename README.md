# Open Reading Source Protocol

**English** · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) ·
[Specification](SPECIFICATION.md) · [中文规范](SPECIFICATION.zh-CN.md) ·
[OpenAPI](openapi.yaml) ·
[Governance](GOVERNANCE.md) · [Ecosystem](ECOSYSTEM.md) ·
[Community Registry](registry/README.md) ·
[中文书源目录](registry/README.zh-CN.md)

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

It implements four core reading operations:

```text
GET {apiBaseUrl}v1/search?q={query}&page=1&pageSize=20
GET {apiBaseUrl}v1/books/{bookId}
GET {apiBaseUrl}v1/books/{bookId}/chapters?page=1&pageSize=100
GET {apiBaseUrl}v1/books/{bookId}/chapters/{chapterId}
```

ORSP 1.1 sources may additionally advertise a standard discovery profile:

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
```

These endpoint relations are resolved against the discovered `apiBaseUrl`.
ORSP 1.1 Core Reading sources implement all four core capabilities. Discovery,
categories, and browsing are optional and capability-gated, so existing ORSP
1.0 sources remain compatible.

Readers may aggregate several sources into an all-sources discovery view and
offer a single-source filter. Aggregate interfaces retain source attribution,
keep IDs source-scoped, preserve each source's internal ranking, and use a
source-balanced merge for latest or popular feeds.

Example discovery document:

```json
{
  "protocol": "open-reading-source",
  "protocolVersion": "1.1",
  "id": "org.example.public-books",
  "name": "Example Public Books",
  "description": "Public-domain books maintained by Example.org",
  "apiBaseUrl": "https://books.example.org/api/",
  "languages": ["en"],
  "capabilities": [
    "search", "discover", "categories", "browse",
    "detail", "catalog", "content"
  ]
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
OEP-0001-discovery.md         ORSP 1.1 discovery proposal and compatibility analysis
openapi.yaml                  OpenAPI 3.1 API description
schemas/discovery.schema.json Discovery-document JSON Schema
examples/dart_server.dart     Runnable reference source
tool/conformance_test.dart    End-to-end core conformance checks
GOVERNANCE.md                 Protocol change and release process
ECOSYSTEM.md                  Adapter and federated registry architecture
registry/                     PR-based community source registry
```

## Status

Protocol version `1.1` is a candidate draft. Its compatibility rules,
machine-readable contracts, reference source, and core conformance tests are
now developed together. Independent reader and source implementations are
welcome before the specification is declared stable.

Run the local conformance checks with:

```bash
dart run tool/conformance_test.dart
```

Traditional book-source formats belong in server-side ORSP adapters rather than
inside readers. Source discovery communities can operate multiple federated
registries; registries do not redefine the wire protocol. See
[ECOSYSTEM.md](ECOSYSTEM.md).

Source operators can submit an ORSP service through a pull request to the
[community registry](registry/README.md). Each source uses one independently
validated manifest file, and the combined reader-facing index is generated
automatically.

## Responsible use

ORSP is intended for original, public-domain, and properly licensed content.
Do not use it to bypass access controls, violate provider terms, or distribute
content without permission.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Protocol changes should include a clear
compatibility analysis and updated examples or schemas.

## License

[MIT](LICENSE)
