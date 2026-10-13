# Origo Source

**Origo Source (元源)** is the public name of this source ecosystem. Its HTTP
contract remains **Open Reading Source Protocol (ORSP)**. Existing discovery
identifiers, paths, headers and source IDs do not change with the human name.

**English** · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) ·
[日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) ·
[Specification](SPECIFICATION.md) · [中文规范](SPECIFICATION.zh-CN.md) ·
[OpenAPI](openapi.yaml) ·
[Governance](GOVERNANCE.md) · [Ecosystem](ECOSYSTEM.md) ·
[Source policy](SOURCE_POLICY.md) ·
[中文书源政策](SOURCE_POLICY.zh-CN.md)

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

ORSP 1.6 sources may additionally advertise standard discovery and rankings
profiles:

```text
GET {apiBaseUrl}v1/discover
GET {apiBaseUrl}v1/categories
GET {apiBaseUrl}v1/browse?category={categoryId}&sort=latest&page=1&pageSize=20
GET {apiBaseUrl}v1/rankings
GET {apiBaseUrl}v1/rankings/{rankingId}?page=1&pageSize=20
```

These endpoint relations are resolved against the discovered `apiBaseUrl`.
ORSP 1.6 Core Reading sources implement all four core capabilities. Discovery,
categories, browsing, and multiple rankings are optional and capability-gated,
so existing ORSP 1.x sources remain compatible.

Readers may aggregate several sources into an all-sources discovery view and
offer a single-source filter. Aggregate interfaces retain source attribution,
keep IDs source-scoped, preserve each source's internal ranking, and use a
source-balanced merge for latest or popular feeds.

The optional `rankings` capability exposes multiple named, paginated ranking
snapshots such as weekly popularity and monthly new releases. Rank values stay
scoped to their source, ranking ID, and snapshot; readers do not treat metrics
from independent sources as one authoritative global chart.

Example discovery document:

```json
{
  "protocol": "open-reading-source",
  "protocolVersion": "1.6",
  "id": "org.example.public-books",
  "name": "Example Public Books",
  "description": "Public-domain books maintained by Example.org",
  "apiBaseUrl": "https://books.example.org/api/",
  "operatorName": "Example Public Books Foundation",
  "contactUrl": "https://books.example.org/rights",
  "contentLicense": "Public Domain",
  "rightsStatement": "This source serves verified public-domain books.",
  "languages": ["en"],
  "maxCatalogPageSize": 200,
  "capabilities": [
    "search", "discover", "categories", "browse", "rankings",
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
OEP-0001-discovery.md         Historical ORSP 1.1 discovery proposal and compatibility analysis
OEP-0007-rankings.md          ORSP 1.6 multiple-ranking proposal and compatibility analysis
openapi.yaml                  OpenAPI 3.1 API description
schemas/discovery.schema.json Discovery-document JSON Schema
examples/dart_server.dart     Runnable reference source
tool/conformance_test.dart    End-to-end core conformance checks
tool/discovery_conformance_test.dart Discovery Profile conformance checks
GOVERNANCE.md                 Protocol change and release process
ECOSYSTEM.md                  Adapter and federated registry architecture
registry/                     Non-official registry reference format and tools
```

## Status

Protocol version `1.6` is a candidate draft. Its compatibility rules,
machine-readable contracts, reference source, and core conformance tests are
now developed together. Independent reader and source implementations are
welcome before the specification is declared stable.

Run the local conformance checks with:

```bash
dart run tool/conformance_test.dart
dart run tool/discovery_conformance_test.dart
```

Traditional book-source formats belong in server-side ORSP adapters rather than
inside readers. Source discovery communities can operate multiple federated
registries; registries do not redefine the wire protocol. See
[ECOSYSTEM.md](ECOSYSTEM.md).

This project does not operate an official source directory and does not accept
source-listing submissions. The `registry/` directory is reference tooling for
independent communities only; the official Open Reading app does not consume
its generated output. See [SOURCE_POLICY.md](SOURCE_POLICY.md).

## Responsible use

ORSP is intended for original, public-domain, and properly licensed content.
Do not use it to bypass access controls, violate provider terms, or distribute
content without permission.

Protocol conformance is not legal certification. Source operators remain
responsible for their content, and users independently choose every source they
add.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Protocol changes should include a clear
compatibility analysis and updated examples or schemas.

## License

[MIT](LICENSE)

## EPUB and community extensions

[OEP-0004](OEP-0004-publications-and-comments.md) adds experimental immutable EPUB downloads and draft work/paragraph comment contracts while preserving ORSP 1.6 core. [Yuanchuang manifest](examples/yuanchuang-source.json) is a working first-party source example. Comment capabilities are not deployed. Run `scripts/validate_creator_extensions.py` alongside existing validation.

## Chapter updates

[OEP-0005](OEP-0005-chapter-updates.md) adds experimental chapter-update state, catalog snapshot pinning and per-chapter text versions. Existing readers keep the core catalog path. Run `python scripts/validate_chapter_updates.py` for live append/correction/pagination checks.

## Complete reading bundle

The 1.6 candidate brings together text/illustrated chapters, chapter updates,
EPUB publications, image sequences, recorded audio and multiple rankings.
Optional profiles preserve existing 1.x endpoint and identity semantics.
See [OEP-0006](OEP-0006-media-reading.md), [OEP-0007 rankings](OEP-0007-rankings.md),
the [source upgrade guide](docs/source-upgrade-guide.zh-CN.md),
[Schema index](docs/Schema.md) and [API index](docs/api.md).
OEP-0007 avoids a collision with the existing registry-diagnostics OEP-0003.

```bash
python examples/reading_profiles_server.py
python scripts/validate_reading_profiles.py
python scripts/test_probe_source.py
python scripts/probe_source.py https://books.example.org/.well-known/open-reading-source.json
```

The reference uses original text, generated PNG/WAV assets and a deterministic
EPUB. Its real HTTP tests cover media expiry, ranges, body corrections and
ranking snapshots. The bounded, read-only probe reports structure without
retaining chapter bodies. Sampled compatibility does not prove every asset or
physical-device playback. Protocol updates do not deploy third-party sources.

## Source builder Skill

`skills/origo-source-builder/` includes a runnable, file-backed core/text source, chapter updates, scaffolding and canonical profile references. Build from a committed ref with `python scripts/build_source_skill.py`; validate scaffolding and real HTTP with `python scripts/validate_source_skill.py`. The website presents Origo Source at [open.xxread.top/sources](https://open.xxread.top/sources).
