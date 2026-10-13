# OEP-0005: Chapter updates and consistent catalog refresh

Status: **Experimental**
Target: optional `top.xxread:chapter-updates` profile on ORSP 1.x.

[中文合同](docs/chapter-updates.zh-CN.md) ·
[Schema](schemas/chapter-updates.schema.json) ·
[OpenAPI](chapter-updates.openapi.yaml) ·
[Reference server](examples/chapter_updates_server.py)

## Problem and compatibility

`updatedAt`, chapter count, and the latest chapter name alone cannot identify
every change: an author may correct an existing chapter, insert a chapter in
the middle, rename/reorder chapters or withdraw one without changing the tail.
Per-page HTTP ETags also identify different representations; equality across
different page URLs is not a valid test of catalog consistency.

Keep every core relation and required field. Sources advertise the namespaced
capability only after implementing this profile. Old readers ignore new fields
and continue fetching complete catalogs through the existing endpoints. No
global push service, authenticated writes or scrape rules are introduced.

## Update state

`GET v1/books/{bookId}/updates` returns:

```json
{
  "bookId": "book-1",
  "catalogVersion": "catalog-12",
  "chapterCount": 2,
  "updatedAt": "2026-10-13T08:00:00Z",
  "latestChapter": {
    "id": "chapter-2", "title": "A second chapter", "order": 1,
    "contentVersion": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }
}
```

`bookId`, `catalogVersion` and `chapterCount` are required. `catalogVersion` is
an opaque 1–200-character unreserved ASCII token, scoped to the source and book;
clients compare equality only, not time, numeric order or tokens across books.
It MUST change whenever chapter IDs, titles, ordering, body representations or
publication artifacts change. It MUST remain stable across unchanged reads.
`chapterCount` counts available catalog entries. If count is zero,
`latestChapter` MUST be absent; otherwise it MUST identify the last chapter in
the current `(order,id)` sort. `updatedAt` is optional and MUST describe an
actual known source modification, never the time of checking or a made-up clock.

Source detail SHOULD additionally expose `catalogVersion`, `chapterCount` and
an actual `updatedAt`; the existing book `latestChapter` remains a title string,
not the update endpoint's object. Search/browse may omit state to avoid N+1
catalog reads. Sources MUST NOT reinterpret the old latestChapter field.

Update state SHOULD provide ETag and `Cache-Control: no-cache`, and honor
`If-None-Match` with 304 on an unchanged representation. Unknown books or private
works return 404. ETags are URI/representation validators, not catalog versions.
Cached state cannot acknowledge a newer catalog without a successful validation.

## Catalog and chapter versions

With this capability, every catalog page additionally includes `catalogVersion`,
and each chapter includes `contentVersion`. Chapter content also includes the
same `contentVersion`. It is the lowercase SHA-256 of the exact UTF-8 `content`
string; no newline or Unicode normalization is implicit. For non-text chapters,
sources MUST define a compatible versioned extension before advertising this
profile; this experiment covers text/plain, text/markdown and text/html only.
Title/order changes update the catalogVersion even if contentVersion is unchanged.
Reliable per-chapter `updatedAt` SHOULD be exposed for existing readers.

IDs identify logical chapters, not array indexes or publication time. Appending,
inserting, renaming, reordering and correcting text MUST preserve existing
chapter IDs. Deleted IDs MUST NOT be reused for another logical chapter. An
EPUB replacement may change package/derived chapter identities; sources MUST
change catalogVersion/publication identity and clients MUST NOT treat every new
derived ID as a newly written chapter without a confirmed mapping.

Clients MAY pin either existing endpoint to a version:

```text
GET v1/books/{bookId}/chapters?page=2&pageSize=100&catalogVersion=catalog-12
GET v1/books/{bookId}/chapters/{chapterId}?catalogVersion=catalog-12
```

This query parameter is available only when the capability is advertised. A
source MUST either serve that exact immutable version or return 409 with the
core error envelope and code `X_CATALOG_VERSION_CONFLICT`. It MUST NOT ignore the
parameter and return a different snapshot. Malformed tokens return 400
`INVALID_PARAMETER`. Version checking precedes conditional response handling:
an obsolete version cannot produce 304. Retaining historical snapshots is
optional; a source may support only its current version. Sources read chapter
metadata and revisions consistently, then compare and serve the same snapshot.

## Reader refresh algorithm

1. Keep a confirmed catalog baseline and its source/book identity. On an
   explicit update check or a bounded scheduled check, revalidate update state.
   On first discovery, create a baseline; do not mark the whole book as new.
2. If catalogVersion is unchanged, retain catalog and cached chapter content.
   Otherwise fetch the catalog pinned to that version, comparing every returned
   page's catalogVersion. Never join pages from different versions. A conflict
   restarts state/catalog fetch with bounded retries; do not busy-loop on updates.
3. Compare complete catalogs by chapter ID. New IDs are additions, missing IDs
   are withdrawals, and changed contentVersion invalidates that chapter's text
   cache even when ID/count/latest title are unchanged. Title/order changes
   refresh metadata. Chapter counts alone MUST NOT be used to classify changes.
4. Preserve unchanged chapter caches and all canonical progress/annotations.
   Revision-bound anchors require conflict/relocation handling, as in OEP-0004;
   never reset progress to a page number or silently move a comment.
5. Publish a new baseline only after a complete validated refresh; retain the
   prior state on network failures and mark it stale. Remove an update badge only
   after the client has loaded the corresponding latest catalog. Locally edited
   downloads still use explicit download/merge and conflict confirmation.

Old sources/readers fall back to fresh core catalog reads and stable IDs plus
updatedAt when available. This profile cannot make an offline reader see changes
or require instantaneous polling; intervals, manual refresh, background limits
and HTTP 429 Retry-After are client policy. Do not rewrite caches on every read.

## Validation and implementations

`python scripts/validate_chapter_updates.py` validates Schema/OpenAPI and runs an
actual HTTP reference server through append, same-count correction, rename,
middle insertion, reorder, deletion, zero chapters, 304, stale-version conflict,
multi-page changes and legacy endpoint cases. Production Yuanchuang implements
the same profile in the independent `origo-creator` repository,
`origo_creator/source_routes.py`, with repeatable database snapshots. A protocol extension does not itself upgrade a reader's UI.

References: [HTTP conditional requests, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-conditional-requests)
and [OEP-0004](OEP-0004-publications-and-comments.md).
