# OEP-0004: EPUB publications, comments and paragraph anchors

Status: **Experimental** for publications; **Draft** for comments  
Target: optional extensions to **ORSP 1.5**; core endpoint relations remain unchanged.

[简体中文合同](docs/publications-and-comments.zh-CN.md) ·
[JSON Schema](schemas/creator-extensions.schema.json) ·
[OpenAPI](extensions.openapi.yaml)

## Compatibility and capability negotiation

This proposal follows the namespaced extension process in GOVERNANCE.md. It
does not silently declare a new stable core version. Sources continue to expose
search, detail, catalog and chapter content to ORSP 1.x readers. Legacy readers
ignore extension fields and capabilities. File downloads MUST NOT replace a
chapter response with ZIP bytes or change the meaning of `contentType`.

| Capability | Meaning | Dependency |
| --- | --- | --- |
| `top.xxread:publications` | Complete, immutable EPUB downloads | Core reading |
| `top.xxread:comments` | Read published work comments | Core reading |
| `top.xxread:paragraph-comments` | Read comments on canonical text ranges | `top.xxread:comments` |
| `top.xxread:comment-write` | Authenticated comment creation/deletion | `top.xxread:comments` |

Clients MUST call optional relations only when the source declares their
capability. A source MUST advertise implemented behavior only. Yuanchuang
currently advertises publications, not comments, paragraph comments or writes.
The core remains 1.5, including existing candidate rankings work.

## Publications (experimental)

`GET v1/books/{bookId}/publications` returns `{ "items": [Publication] }`.
Book detail MAY also include the same `publications` array. Empty means this
book has no complete EPUB representation. A Publication contains a stable
opaque `id`, absolute HTTPS `href`, `mediaType: application/epub+zip`, positive
`bytes`, and lowercase 64-character `sha256`. The hash and byte length describe
the complete downloaded file, not the JSON metadata or decompressed resources.
Clients MUST bound download size, verify both length and hash before importing,
and use their existing EPUB reader. Content updates allocate a new publication
ID; a publication ID MUST NOT be reused for different bytes.

Yuanchuang uses `GET v1/books/{bookId}/publications/{publicationId}` for the
binary representation. Other sources MAY use another absolute `href`.
Download responses use the EPUB MIME type and SHOULD provide Content-Length,
ETag, Content-Disposition and HTTP byte-range support. Sources retain core
chapter access: text projection is useful to existing readers, but MUST NOT be
presented as a lossless EPUB rendering. Unsupported non-text or oversized
publications MAY be downloaded, with core projection limitations disclosed.
Redirects follow the core security rules; client credentials MUST NOT cross
origins. Source relocation changes URLs, not book/publication identities.

## Comments (draft; not a deployed service)

`GET v1/books/{bookId}/comments?limit=20&cursor=...` returns
`{ "items": [Comment], "hasMore": false }`. Limit is 1–100. A next page
includes opaque `nextCursor` iff `hasMore` is true. Ordering is descending
`(createdAt, id)`; cursor identifies that boundary and the selected filter.
Concurrent inserts cannot duplicate earlier items. A cursor reused for another
book/filter is invalid. `chapterId` is an optional query parameter available
only with paragraph-comments; it selects comments anchored to that chapter.
Unfiltered results may contain both whole-work and paragraph comments.

A Comment contains stable `id`, `bookId`, `author` (`id`, `displayName`), plain
`body` (1–4000 Unicode scalar values), `createdAt` (RFC 3339), and optional
`replyTo` / `anchor`. Public author data never contains emails, account tokens,
device identifiers or client-supplied identity claims. Replies stay in the same
book and copy their root anchor. Deleted/removed bodies are omitted from public
lists; replies may retain an opaque replyTo reference to an absent comment.
Counts describe published comments only. Reads never grant write authority.

`POST v1/books/{bookId}/comments` accepts `{body, replyTo?, anchor?}` and an
`Idempotency-Key` UUID. Same actor/key/body replays the original result; a changed
payload returns 409. A server derives author identity from a validated token,
checks book visibility, anchor revision, reply ownership and limits, and returns
201 for a published Comment. An implementation with moderation MUST NOT claim
this write contract until it defines a separate pending-submission response.
`DELETE v1/books/{bookId}/comments/{commentId}` returns 204 after owner/moderator
authorization and is idempotent for that actor. Read/write limits, reporting,
moderation, blocking and data deletion must be implemented before public writes.

Write authentication is a separate source contract. Sources MUST document
trusted issuer, audience, scopes and revocation; clients MUST obtain a token
explicitly issued for that source and MUST NOT forward an existing Origo token
to arbitrary sources. Credentials are never placed in JSON manifests or URLs.
Browser writers also need a defined origin/CSRF policy. This draft does not
introduce global SSO or require unrelated ORSP sources to use Origo accounts.

## Paragraph anchors (draft)

Text targets use `{chapterId, contentVersion, selector}`. With paragraph-comments,
chapter content additionally provides `canonicalText` and `contentVersion`.
`canonicalText` is versioned semantic source text, independent of pages, fonts,
DOM IDs, renderer whitespace and device layout. Its exact UTF-8 SHA-256 is
`contentVersion`; no implicit Unicode normalization is applied. A selector has
`type: TextPositionSelector`, nonnegative `start`, exclusive `end > start`, and
`quote: {exact, prefix?, suffix?}`. Offsets count Unicode scalar values, not
UTF-16 code units or UTF-8 bytes. `exact` MUST match canonicalText[start:end].
Markdown providers MUST define the source-to-rendered text mapping; a client
MUST NOT assume raw Markdown offsets equal rendered offsets.

EPUB targets may alternatively use `type: EpubCfiSelector`, `publicationId`,
relative package `resource` and `cfi`. The anchor contentVersion is the immutable
publication SHA-256 in that case. The resource must identify an actual manifest
document, and its CFI must resolve inside that publication. A CFI and a text
offset are distinct locators; servers/clients MUST NOT silently convert between
them. UUID identities and revision hashes never depend on device page numbers.

An outdated version or mismatched quote returns 409 `X_ANCHOR_CONFLICT`. Readers
may use prefix/suffix/quote to propose relocation but MUST NOT silently attach
an ambiguous comment to a different paragraph. Edits create new revisions;
historical anchors remain bound to their original revision. Full books,
articles and serial novels use the same anchor and comment structure.

## Errors and validation

Extensions preserve the core `{error:{code,message,retryable?}}` envelope.
Additional source-specific codes: `X_PUBLICATION_NOT_FOUND` (404),
`X_COMMENT_NOT_FOUND` (404), `X_AUTH_REQUIRED` (401), `X_FORBIDDEN` (403),
`X_ANCHOR_CONFLICT` (409), `X_IDEMPOTENCY_CONFLICT` (409). Parameter errors remain
400 `INVALID_PARAMETER`; rate limits remain 429 with Retry-After.
The Schema checks structure; semantic range/quote/revision, authentication and
capability dependencies require conformance checks as documented above.

## Implementation evidence

Yuanchuang: `F:/code/Origo-Reader/platform/origo_platform/source_routes.py`,
`epub_projection.py`, and tests `test_source.py`. Existing Origo X 1.x import,
catalog and chapter model parsers can consume the deployed source without a new
application binary. Public EPUB download works now; native file-download UI
and comment/paragraph UI are separate follow-up implementations.

References: [EPUB 3.3](https://www.w3.org/TR/epub-33/),
[W3C Web Annotation selectors](https://www.w3.org/TR/annotation-model/#selectors).
ORSP uses a small transport-specific contract informed by these specifications,
not a claim of full Web Annotation JSON-LD conformance.
