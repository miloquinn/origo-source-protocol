# Origo Source Protocol 1.6

[简体中文翻译](SPECIFICATION.zh-CN.md)

Status: **Candidate draft**

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, and MAY in this
document are to be interpreted as described in RFC 2119 and RFC 8174 when, and
only when, they appear in all capitals.

## Names and secure transport

The product is **Origo X**; the source ecosystem is **Origo Source (元源)**.
ORSP means **Origo Source Protocol**. New sources MUST use `protocol:
origo-source` at `/.well-known/origo-source.json`. New clients MUST accept both
`origo-source` and the legacy `open-reading-source` identifier. The 1.x JSON
semantics and `v1/...` relations are unchanged. Unknown identifiers MUST be
rejected. Branding changes MUST NOT reassign stable source, book or chapter IDs.

To serve installed readers, a new 1.x source MUST also expose
`/.well-known/open-reading-source.json` with `protocol: open-reading-source` and
the same source ID, origin, API base and capabilities. This is a compatibility
alias, not a separate source or a redirect to a new discriminator. Old sources
remain valid without implementing the new alias. New response headers use
`X-Origo-Source-Protocol`; sources SHOULD emit the equivalent legacy
`X-Open-Reading-Protocol` header during migration. The legacy
`X-Open-Reading-Request-Purpose` header has the same advisory semantics as
`X-Origo-Source-Request-Purpose`; the canonical header takes precedence.

Both `http://` and `https://` URLs are supported; “HTTP” in endpoint and status
descriptions denotes HTTP semantics over either transport. Public production
sources SHOULD use HTTPS for discovery, APIs, publications and media assets.
HTTPS clients MUST verify the certificate chain and hostname. Sources SHOULD
support TLS 1.2 or later; reverse proxies may terminate TLS while the private
upstream uses HTTP. Local development MAY use HTTP. Clients MUST NOT silently
downgrade an HTTPS request to HTTP. HTTP/2 and HTTP/3 may be negotiated by the
hosting layer and MUST NOT change the JSON contract or become a core requirement.

## 1. Scope and design goals

Origo Source Protocol (ORSP) defines a safe HTTP(S) boundary between a
reading client and an independently operated content source. ORSP 1.6 covers:

- source discovery;
- book search and metadata;
- optional curated discovery, categories, browsing, and multiple rankings;
- chapter catalogs;
- chapter content retrieval.

The complete reading bundle also specifies optional, namespaced companion
profiles for EPUB publications (OEP-0004), chapter updates (OEP-0005), and image
sequences / recorded audio (OEP-0006). They remain experiments, separately
declared and tested; they do not become mandatory core requirements.

ORSP 1.6 covers public HTTP(S) sources that do not require user authentication.
It does not define executable scraping rules. A source MAY use an authorized
adapter internally, but clients only receive data described by this protocol.

The core reading profile is intentionally small. A conforming ORSP 1.6 source
MUST implement the complete discovery, search, detail, catalog, and content
path. Optional features are advertised as capabilities and MUST NOT change the
meaning of core fields or endpoints.

## 2. Protocol versions and evolution

Protocol versions use `MAJOR.MINOR`, for example `1.0`. They are not Semantic
Versioning package versions and MUST NOT include a patch component.

- A major version may make incompatible changes.
- A minor version may add optional object members, optional capability tokens,
  optional endpoints, or additional enum values with defined fallback behavior.
- A minor version MUST NOT remove or reinterpret an existing field, make an
  optional field required, or change the meaning of an existing HTTP status.
- A minor version MUST NOT add a request query parameter to an existing
  endpoint except as part of a new capability token. A client MUST NOT send
  such a parameter to a source that does not advertise the corresponding
  capability. This keeps parameter support explicit: a source never silently
  ignores a parameter whose effect the client depends on.

A client implementing ORSP 1.x SHOULD accept any discovery document with major
version `1`. This is safe only because all 1.x implementations MUST follow the
forward-compatibility rules in this document.

`protocolVersion` identifies the protocol version the discovery document
itself conforms to. A source that implements more than one protocol version
SHOULD also list every implemented version in the optional
`supportedVersions` discovery member (Section 3). Endpoint relations carry
their own major-version prefix (`v1/...`), so one `apiBaseUrl` can serve
several major versions side by side. Complete cross-major negotiation rules
are reserved future work (Section 17); within major version 1,
`supportedVersions` is informative.

Clients MUST ignore unknown JSON object members. Clients MUST ignore unknown
optional capability tokens. A source MUST NOT require an extension capability
for discovery, search, detail, catalog, or content in the core reading profile.

Missing and `null` are different values. Sources MUST omit an unavailable
optional member. A source MUST NOT emit `null` unless the member's schema
explicitly permits it.

## 3. Discovery

A source MUST expose a JSON discovery document at the origin-root path:

```text
/.well-known/origo-source.json
```

Clients MAY also accept a complete discovery-document URL supplied by a user or
registry. Redirect handling is defined in Section 5.

Required discovery members:

| Member | Requirement |
| --- | --- |
| `protocol` | MUST equal `origo-source` |
| `protocolVersion` | ORSP `MAJOR.MINOR`; this specification uses `1.6` |
| `id` | Stable globally unique source identifier |
| `name` | Human-readable source name |
| `apiBaseUrl` | Absolute HTTP(S) URL ending in `/` |
| `capabilities` | MUST contain all four core capability tokens |

Core capability tokens are `search`, `detail`, `catalog`, and `content`.

ORSP 1.6 defines four optional standard capability tokens:

| Capability | Endpoint relation | Purpose |
| --- | --- | --- |
| `discover` | `v1/discover` | Curated shelves such as featured or popular books |
| `categories` | `v1/categories` | Stable category identifiers and display names |
| `browse` | `v1/browse` | Paginated browsing by category or standard sort |
| `rankings` | `v1/rankings` | Multiple named, paginated ranking lists |

A source declaring `categories` MUST also declare `browse`, because category
identifiers are defined for use with the browse endpoint. A source MAY declare
`browse` without `categories`, for example to expose only a latest-updates
feed. These capabilities are optional: their absence MUST NOT affect core
search or reading behavior.

Extension capability tokens MUST use a collision-resistant namespace in the
form `reverse.domain:name`, for example `org.example:audio`. An extension token
MUST NOT use the `orsp` namespace unless it is defined by a future ORSP
specification. Unknown extension tokens do not make a source incompatible.

Optional discovery members are `description`, `iconUrl`, `websiteUrl`,
`languages`, `supportedVersions`, `maxCatalogPageSize`, `operatorName`,
`contactUrl`, `contentLicense`, `rightsStatement`, and `contentTypes`. Language tags MUST
follow BCP 47, such as `en`, `zh-CN`, or `sr-Latn`.

`contentTypes`, when present, lists the chapter representations emitted by the
source, not downloadable publication MIME types. It is a nonempty unique array
of at most 32 lowercase media type strings. Its absence on older sources means
unspecified, not empty. Clients MUST ignore unfamiliar declared types during
source import, but MUST explicitly reject unsupported types when opening a
chapter. `image/sequence` requires `top.xxread:image-sequence`; `audio/uri`
requires `top.xxread:remote-audio`. Either media capability requires
`contentTypes` to include the corresponding type. This is an advertisement,
not an Accept-based representation negotiation mechanism.

`supportedVersions`, when present, is a non-empty array of ORSP
`MAJOR.MINOR` version strings that MUST include `protocolVersion`. It lets a
multi-version source state every protocol version it implements. ORSP 1.6
clients MAY use it for diagnostics and MUST NOT require it.

`maxCatalogPageSize`, when present, is an integer between 1 and 1000
declaring the largest `pageSize` the source accepts on the chapter-catalog
endpoint (Section 12). When absent, the limit is 100.

`operatorName`, `contactUrl`, `contentLicense`, and `rightsStatement` are
rights-transparency members. `operatorName` identifies the entity that
actually operates the source and can act on rights requests. `contactUrl`,
when present, MUST be an absolute HTTP(S) URL for a contact or rights-report
page controlled by that operator. `contentLicense` is a short license name or
authorization basis, for example `CC BY 4.0` or `Public Domain`.
`rightsStatement` is a concise, source-supplied description of content
provenance or authorization scope. A client MAY display these members for
transparency but MUST NOT treat their presence, absence, or content as a
legality, authorization, or identity certification by any reader, registry,
or the protocol itself.

`apiBaseUrl` MUST NOT contain user information, a query, or a fragment and MUST
end in `/`. Endpoint paths in this document are resolved relative to that URL.
For example, an API base URL of `https://books.example/api/` and endpoint
relation `v1/search` produce `https://books.example/api/v1/search`.

The source `id` MUST be between 3 and 200 characters, start and end with an
ASCII letter or digit, and otherwise contain only ASCII letters, digits, `.`,
`_`, or `-`. It MUST remain unchanged when the source host, API URL, or display
name changes. Reverse-domain form is recommended. Source IDs identify a source
only; book and chapter IDs are scoped to that source.

No central authority allocates source IDs, so a client can encounter two
different sources claiming the same `id`. Clients MUST NOT treat the `id`
alone as a storage key. A client MUST key stored source state on at least the
pair of `id` and the discovery-document origin, MUST NOT silently merge or
replace an installed source when a different origin presents the same `id`,
and SHOULD surface such a collision to the user. Two discovery documents
describe the same source only when both the `id` and the origin match.

The discovery document is formally described by
[`schemas/discovery.schema.json`](schemas/discovery.schema.json).

## 4. Data model and encoding

### 4.1 JSON and text

- Requests and responses MUST use UTF-8.
- JSON responses MUST use `application/json`; media type parameters such as
  `charset=utf-8` are allowed.
- JSON object member names are case-sensitive.
- Clients MUST ignore unknown object members at every nesting level.
- Sources SHOULD normalize human-readable text to Unicode NFC.
- Timestamps MUST be RFC 3339 `date-time` values. UTC with a `Z` suffix is
  recommended.

### 4.2 Identifiers

Book and chapter IDs are stable opaque strings. To produce identical routing
behavior across common HTTP frameworks, wire IDs MUST contain only RFC 3986
unreserved ASCII characters: letters, digits, `-`, `.`, `_`, and `~`.

IDs MUST be between 1 and 200 characters. Clients MUST treat each ID as one URL
path segment and MUST NOT infer hierarchy or other meaning from it. A source
MUST NOT reuse an ID for a different logical resource.

Chapter IDs are unique within a book. Book IDs are unique within a source.

### 4.3 URLs

JSON URL members MUST be absolute HTTP(S) URLs unless a field explicitly says
otherwise. Clients MUST reject unsupported URL schemes. Clients SHOULD apply
platform-appropriate limits before downloading covers or other remote assets.

### 4.4 Enums

For descriptive enums that include the value `unknown`, clients MUST map an
unrecognized value to `unknown`. For operational enums such as `contentType`, a
client MUST report that the representation is unsupported rather than guessing
how to interpret it.

## 5. HTTP behavior

- Core endpoints use `GET` and MUST be safe and idempotent.
- Clients SHOULD send `Accept: application/json`.
- Clients SHOULD send `X-Origo-Source-Protocol` with their highest supported
  ORSP 1.x version, for example `1.6`.
- Sources MAY return `X-Origo-Source-Protocol` containing the source protocol
  version.
- A client or operator probe MAY send `X-Origo-Source-Request-Purpose:
  health-check`. Sources SHOULD exclude requests with this value from
  reader-facing analytics and rankings. The header is advisory only and MUST
  NOT grant access, bypass rate limits, or alter content authorization.
  Requests without it are user requests.
- Unsupported methods MUST return `405 Method Not Allowed` and SHOULD include
  an `Allow` header.
- Sources SHOULD support HTTP compression for large JSON responses.

Clients MAY follow redirects, subject to all of the following:

- no more than five redirects per request;
- redirect targets MUST use HTTP(S);
- clients MUST NOT silently follow an HTTPS-to-HTTP downgrade;
- credentials or private headers MUST NOT be forwarded to a different origin.

Clients SHOULD enforce configurable connection, response-time, decompressed
size, and redirect limits. A client MUST treat all source responses as
untrusted input.

### 5.1 Caching

Discovery documents, discovery shelves, categories, browse pages, detail,
catalog, and content responses SHOULD provide an `ETag` or appropriate
`Cache-Control`/`Last-Modified` headers. When a client sends `If-None-Match`
with a current entity tag, a source SHOULD return `304 Not Modified` with no
response body.

An entity tag identifies the complete selected representation. Sources MUST
change it when a response changes in a way visible to a client.

## 6. Search

Endpoint relation:

```text
GET v1/search?q={query}&page={page}&pageSize={pageSize}
```

`q` is required after trimming surrounding whitespace and MUST contain between
1 and 200 Unicode scalar values. `page` starts at 1 and defaults to 1.
`pageSize` defaults to 20 and MUST be between 1 and 100.

Sources MAY ignore unknown query parameters. Sources MUST return `400` for an
invalid known query parameter.

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
      "language": "en",
      "updatedAt": "2026-07-11T10:00:00Z"
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1,
  "hasMore": false
}
```

`items`, `page`, `pageSize`, and `hasMore` are required. `pageSize` reports the
requested page capacity, not the number of returned items. `total` is optional
because some sources cannot calculate it efficiently. Search ranking is
source-defined but SHOULD be deterministic for an unchanged dataset and query.

Book objects MUST include `id` and `title`. Other members are optional.
`language`, when present, MUST be a BCP 47 tag. `status` is one of `ongoing`,
`completed`, `hiatus`, or `unknown`.

## 7. Curated discovery (optional)

Sources declaring `discover` MUST implement:

```text
GET v1/discover
```

Response:

```json
{
  "sections": [
    {
      "id": "featured",
      "title": "Featured",
      "items": [
        {
          "id": "book-1001",
          "title": "Example Book",
          "author": "Example Author"
        }
      ]
    }
  ]
}
```

`sections` is required. Each section MUST contain `id`, `title`, and `items`.
Section IDs follow the opaque wire-ID rules in Section 4.2, are scoped to the
source, and SHOULD remain stable when the display title changes. Section titles
are human-readable and MAY be localized according to the source's content
policy. Empty sections SHOULD be omitted.

Each section MAY contain at most 100 books. Book objects use the same model as
search and detail. Section ordering and item ranking are source-defined but
SHOULD be deterministic for an unchanged dataset. Clients MUST NOT interpret a
section as personalized unless the source explicitly documents that behavior;
ORSP 1.6 does not define authentication or user profiles.

## 8. Categories (optional)

Sources declaring `categories` MUST implement:

```text
GET v1/categories
```

Response:

```json
{
  "items": [
    {"id": "fiction", "name": "Fiction"},
    {"id": "history", "name": "History"}
  ]
}
```

`items` is required. Category IDs follow the opaque wire-ID rules in Section
4.2 and MUST be accepted unchanged as the `category` browse parameter.
Category names are human-readable. Sources SHOULD keep IDs stable when names
change. Category ordering is source-defined and SHOULD be deterministic.

## 9. Browse (optional)

Sources declaring `browse` MUST implement:

```text
GET v1/browse?category={categoryId}&sort={sort}&page={page}&pageSize={pageSize}
```

`category` is optional. When present it MUST contain between 1 and 200
characters and identify a category returned by `v1/categories`. A source that
does not declare `categories` MUST return `400` if `category` is supplied.

`sort` is optional and defaults to `latest`. ORSP 1.6 defines:

- `latest`: descending by the book's `updatedAt`, with books lacking
  `updatedAt` ordered after dated books;
- `popular`: source-defined popularity ranking, deterministic for an unchanged
  ranking snapshot.

Sources MUST return `400` for an unsupported sort value. `page` and `pageSize`
use the search pagination rules. The response uses the search-page schema.
When `category` is omitted, the endpoint browses all books visible to the
source under the selected sort.

### 9.1 Multi-source aggregation

A client connected to more than one source MAY present discovery shelves,
categories, or browse results in one aggregate interface. An aggregate client:

- MUST retain the originating source for every section, category, and book;
- MUST treat section, category, and book IDs as source-scoped and MUST NOT
  merge objects solely because their IDs or display names match;
- SHOULD visibly identify the source wherever results from several sources can
  otherwise be confused, and MAY offer an all-sources view plus a single-source
  filter;
- SHOULD preserve each source's response ordering when combining `latest` or
  `popular` feeds and SHOULD use a source-balanced merge so one source cannot
  monopolize the aggregate solely through result volume or timestamps; and
- SHOULD retain successful results when another source times out or fails,
  while making partial failure observable to the user when it affects the
  result.

`updatedAt` establishes ordering within one source's `latest` response. An
aggregate client MAY use it as a cross-source freshness hint, but MUST NOT treat
timestamps from independently operated sources as a globally authoritative
ranking.

## 10. Rankings (optional)

Sources declaring `rankings` MUST implement both ranking endpoint relations:

```text
GET v1/rankings
GET v1/rankings/{rankingId}?page={page}&pageSize={pageSize}
```

The ranking collection response is:

```json
{
  "items": [
    {
      "id": "weekly-popular",
      "title": "Weekly Popular",
      "description": "Most-read books during the current week",
      "period": "weekly",
      "categoryId": "fiction"
    },
    {
      "id": "monthly-new",
      "title": "Monthly New Releases",
      "period": "monthly"
    }
  ]
}
```

`items` is required and MUST contain at most 100 rankings. Each ranking MUST
contain `id` and `title`. Ranking IDs follow the opaque wire-ID rules in
Section 4.2, are scoped to the source, and SHOULD remain stable when display
metadata changes. `description`, `period`, and `categoryId` are optional.

When present, `period` is one of `realtime`, `daily`, `weekly`, `monthly`, or
`all-time`. A ranking whose period does not match one of these values MUST omit
`period` rather than inventing another value. When present, `categoryId` MUST
identify a category returned by `v1/categories`; therefore a source that does
not declare `categories` MUST omit `categoryId`. Ranking collection ordering is
source-defined and SHOULD be deterministic for an unchanged collection.

A ranking page response is:

```json
{
  "ranking": {
    "id": "weekly-popular",
    "title": "Weekly Popular",
    "period": "weekly"
  },
  "snapshotId": "weekly-popular-2026-w30",
  "snapshotAt": "2026-07-26T00:00:00Z",
  "items": [
    {
      "rank": 1,
      "previousRank": 3,
      "score": 9850,
      "scoreLabel": "9,850 reads",
      "book": {
        "id": "book-1001",
        "title": "Example Book"
      }
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1,
  "hasMore": false
}
```

`ranking`, `snapshotId`, `items`, `page`, `pageSize`, and `hasMore` are
required. `ranking` uses the same ranking object returned by `v1/rankings`.
`snapshotId` is an opaque identifier for the ordered ranking snapshot and MUST
remain unchanged while ranks and ordering are unchanged. `snapshotAt` is
optional and records when the snapshot was produced. `total` is optional.

Each entry MUST contain `rank` and `book`. `rank` is the one-based absolute
position in the complete ranking, not the position within the current page.
Entries MUST be returned in ascending `rank` order, ranks MUST be unique within
a snapshot, and the first entry on page N MUST have rank
`(N - 1) * pageSize + 1`. `book` uses the shared book model. `previousRank`,
`score`, and `scoreLabel` are optional. `previousRank`, when present, is the
book's one-based position in the source-defined previous comparable snapshot.
The meaning and scale of `score` and the display text in `scoreLabel` are
source-defined; clients MUST NOT compare them across different rankings or
sources.

`page` and `pageSize` use the search pagination rules. Sources SHOULD return an
`ETag` for the collection and every ranking page. A client loading several
pages MUST compare `snapshotId` values and SHOULD restart from page 1 if the
snapshot changes, to avoid displaying ranks from different snapshots. An
unknown well-formed ranking ID MUST return `404` with `RANKING_NOT_FOUND`.

Ranks are authoritative only inside the tuple of source, ranking ID, and
snapshot ID. An aggregate client MUST retain that attribution and MUST NOT
present ranks from independently operated sources as one globally authoritative
ranking. It MAY show source rankings side by side or build an explicitly
client-generated, source-balanced aggregate view.

## 11. Book details

Endpoint relation:

```text
GET v1/books/{bookId}
```

The response uses the same book object as search and MAY provide a longer
description or additional optional metadata. Existing member meanings MUST be
identical in search and detail responses.

## 12. Chapter catalog

Endpoint relation:

```text
GET v1/books/{bookId}/chapters?page={page}&pageSize={pageSize}
```

`page` defaults to 1. `pageSize` defaults to 100. Its upper bound is the
source's declared `maxCatalogPageSize` (Section 3), or 100 when that member is
absent. A source MUST return `400` for a `pageSize` above its declared bound,
and a client MUST NOT send one. Long serials commonly have thousands of
chapters, so sources able to serve larger pages SHOULD declare a higher bound
to reduce request counts.

```json
{
  "items": [
    {
      "id": "chapter-1",
      "title": "Chapter One",
      "order": 1,
      "updatedAt": "2026-07-11T10:00:00Z"
    }
  ],
  "page": 1,
  "pageSize": 100,
  "total": 1,
  "hasMore": false
}
```

Chapter objects MUST contain `id`, `title`, and `order`. `order` is a
zero-or-positive integer. Sources SHOULD use unique order values within a book.
When order values are equal, clients MUST use the chapter ID as an ascending
secondary sort key so display order remains deterministic.

Catalog pages MUST be sorted by `(order, id)`. A source SHOULD return an `ETag`
for each catalog page. An ETag validates that page's selected representation;
clients MUST NOT compare ETags of different page URLs as one catalog version.
A changed validator on a revalidated page SHOULD restart catalog loading to
avoid a mixed view. Sources SHOULD expose reliable per-chapter `updatedAt` and
refresh validators when chapters are added or corrected.

The optional experimental [OEP-0005 chapter update profile](OEP-0005-chapter-updates.md)
adds update state, consistent catalog versions and per-chapter text versions.
Existing readers continue using core catalog reads; extension-aware clients
send its version query only to sources advertising the capability.

## 13. Chapter content

Endpoint relation:

```text
GET v1/books/{bookId}/chapters/{chapterId}
```

```json
{
  "bookId": "book-1001",
  "chapterId": "chapter-1",
  "title": "Chapter One",
  "contentType": "text/plain",
  "content": "Chapter content",
  "baseUrl": "https://books.example.org/books/book-1001/"
}
```

`bookId` and `chapterId` MUST exactly match the requested resource. `baseUrl` is
optional and, when present, MUST be an absolute HTTP(S) URL.

ORSP 1.6 core text content types are:

- `text/plain`;
- `text/markdown`, interpreted as CommonMark;
- `text/html`, containing an HTML fragment rather than a complete document.

Relative links and image URLs are resolved against `baseUrl` when provided,
otherwise against the final chapter request URL.

HTML MUST NOT contain scripts or other executable content. Sources SHOULD
remove event-handler attributes, dangerous URL schemes, embedded frames, and
active form controls. Clients MUST still sanitize HTML before rendering it.
Raw HTML embedded in Markdown MUST receive the same treatment.

The optional [OEP-0006 media profile](OEP-0006-media-reading.md) defines
`image/sequence` and `audio/uri` without changing this endpoint relation.
Media chapters retain bookId, chapterId and title, leave content empty, and
provide ordered images or a recording descriptor. Sources MUST advertise the
matching media capability. Book `mediaKind` describes text, image-sequence or
remote-audio; unfamiliar values map to unknown. The optional numeric `type`
bridge (8 / 64 / 32) is for existing readers. Recorded audio is distinct from
client TTS, and EPUB is a complete publication, not an audio or ZIP chapter.
Legacy readers continue reading text books and explicitly handle unsupported
media books rather than treating binary content as text.

The profile also defines expiry metadata, bounded chapter refresh, public
request hints and media revision semantics. A media contentVersion is an
opaque revision fingerprint; only an explicitly labeled file sha256 is an
integrity checksum. See the [upgrade guide](docs/source-upgrade-guide.zh-CN.md)
for the capability matrix and runnable acceptance steps.

## 14. Errors

Core status codes:

| Status | Meaning |
| --- | --- |
| `304` | Selected representation has not changed |
| `400` | Invalid request parameter or malformed ID |
| `404` | Book, chapter, ranking, or route not found |
| `405` | HTTP method not supported |
| `429` | Rate limited; `Retry-After` SHOULD be included |
| `500` | Internal source error |
| `503` | Source temporarily unavailable; `Retry-After` MAY be included |

Except for responses that cannot contain a body, error responses MUST use:

```json
{
  "error": {
    "code": "BOOK_NOT_FOUND",
    "message": "The requested book does not exist",
    "retryable": false,
    "requestId": "request-7f3a"
  }
}
```

`code` and `message` are required. Codes MUST use stable uppercase ASCII words
separated by underscores. `message` is intended for developers and diagnostics;
clients SHOULD NOT assume it is localized. `retryable` and `requestId` are
optional. Clients MUST ignore unknown error members and unknown error codes.

ORSP 1.6 defines these standard error codes:

| Code | Status | Condition |
| --- | --- | --- |
| `INVALID_PARAMETER` | `400` | A known query parameter or ID is missing, malformed, or out of range |
| `BOOK_NOT_FOUND` | `404` | The book ID does not identify a book |
| `CHAPTER_NOT_FOUND` | `404` | The chapter ID does not identify a chapter of the book |
| `RANKING_NOT_FOUND` | `404` | The ranking ID does not identify a ranking |
| `ROUTE_NOT_FOUND` | `404` | The path is not an endpoint of this source |
| `METHOD_NOT_ALLOWED` | `405` | The HTTP method is not supported |
| `RATE_LIMITED` | `429` | The client exceeded a request-rate limit |
| `INTERNAL_ERROR` | `500` | An unexpected source-side failure |
| `UNAVAILABLE` | `503` | The source is temporarily unable to serve requests |

When a condition matches a standard code, sources SHOULD return that code and
MUST NOT use a standard code for a different condition. All codes without an
`X_` prefix are reserved for current and future ORSP specifications;
source-defined codes MUST begin with `X_`, for example `X_REGION_BLOCKED`.
Parameter-level detail belongs in `message`.

Sources MUST NOT include credentials, cookies, internal URLs, stack traces, or
other sensitive implementation details in error responses.

## 15. Security and privacy

Sources MUST validate known query parameters and IDs and SHOULD impose rate,
response-size, execution-time, and upstream-fetch limits. Production sources
SHOULD use HTTPS.

Clients accepting user- or registry-supplied source URLs SHOULD protect against
server-side request forgery, DNS rebinding, loopback/private-network access,
redirect loops, decompression bombs, and unexpectedly large images or content.
Whether private-network sources are allowed is a client policy decision and
SHOULD be explicit to the user.

Web-facing sources are responsible for an appropriate CORS policy. CORS is not
required for native clients.

ORSP does not grant copyright or access rights. Source operators are
responsible for distributing only content they are authorized to provide.

## 16. Conformance

An implementation claiming `ORSP 1.6 Core Reading` conformance MUST:

1. implement discovery and all four core capabilities;
2. satisfy the normative requirements in this document;
3. pass the official core conformance suite for the claimed version;
4. disclose optional extension capabilities separately.

An implementation claiming `ORSP 1.6 Discovery` conformance MUST additionally
implement and advertise `discover`, `categories`, and `browse`, and pass the
official discovery-profile checks. A source MAY implement only a subset of the
optional standard capabilities without claiming the complete Discovery
profile.

An implementation claiming `ORSP 1.6 Rankings` conformance MUST additionally
implement and advertise `rankings`, expose at least two ranking definitions,
and pass the official rankings-profile checks. The rankings profile is
independent of the Discovery profile; `categories` is required only when a
ranking uses `categoryId`.

Passing syntax validation alone is not evidence of protocol conformance.
Conformance reports SHOULD record the test-suite version and execution date.

## 17. Reserved future work

The following features are intentionally outside ORSP 1.6 and require a future
minor version, major version, or companion specification:

- authentication and paid-content authorization;
- cross-major version negotiation: rules for choosing an entry point when a
  source advertises several major versions through `supportedVersions`,
  including any per-version endpoint mapping a major version needs;
- request-driven representation selection and fallback negotiation beyond the
  optional contentTypes advertisement;
- localized discovery metadata, such as per-language `name` and `description`
  members;
- cursor-based and incremental catalog synchronization;
- offline package/download manifests;
- source health and registry protocols;
- additional media representations, DRM, and book-level background music;
- annotations, highlights, and reading-progress synchronization.

## Experimental publications and draft comments

[OEP-0004](OEP-0004-publications-and-comments.md) defines namespaced optional publication and comment profiles outside the stable core. These profiles do not change ORSP 1.6 conformance or require existing readers to implement comment authentication.
