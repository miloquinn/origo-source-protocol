# OEP-0004: Multiple named rankings

Status: **Candidate**
Target: **ORSP 1.5**

## Problem

ORSP 1.4 can expose one source-defined `popular` browse ordering and can place
small ranking-like shelves inside `v1/discover`. It cannot let a reader list
multiple ranking resources, paginate a selected ranking, identify the ranking
period, display absolute positions or movement, or detect a snapshot change
while loading several pages.

Encoding rank as a book member would also be incorrect: rank belongs to the
relationship between a book and one source-defined ranking snapshot, not to the
book itself.

## Proposal

Reserve the optional standard capability `rankings` with two endpoint
relations:

| Endpoint | Purpose |
| --- | --- |
| `GET v1/rankings` | List up to 100 named ranking definitions |
| `GET v1/rankings/{rankingId}` | Return one ranking with search-style pagination |

Ranking definitions have stable source-scoped IDs and human-readable titles.
They may declare a standard period (`realtime`, `daily`, `weekly`, `monthly`,
or `all-time`) and may reference a standard category when the source also
declares `categories`.

Ranking pages wrap the shared book model in entries containing an absolute
one-based `rank`. Optional `previousRank`, `score`, and `scoreLabel` members
support movement and source-defined metrics without assigning those meanings
to the book object. Every page includes a required `snapshotId`; clients detect
a changed ordered snapshot and restart pagination instead of mixing ranks.

## Compatibility

- The four core reading capabilities and all ORSP 1.4 endpoint meanings are
  unchanged.
- `rankings` is optional. Older 1.x clients ignore the unknown capability and
  continue using core reading, discovery, and browse behavior.
- A client calls ranking endpoints only after the source advertises
  `rankings`.
- Ranking, page, and entry objects allow unknown members under the existing
  forward-compatibility rules.
- Sources that only need one generic popularity feed may continue to use
  `v1/browse?sort=popular`.

## Multi-source behavior

A rank is authoritative only inside one source, ranking ID, and snapshot ID.
Readers retain all three parts of that attribution. They must not merge ranks
from independent sources into a purported global ranking because the source
populations, metrics, periods, and scores are not directly comparable.

Readers may display source rankings side by side or construct an explicitly
client-generated, source-balanced aggregate view that does not reuse the
source-provided rank numbers as global positions.

## Security and privacy

Both endpoints are safe, idempotent, unauthenticated `GET` operations. The
existing request validation, response-size, caching, rate-limit, SSRF, and
untrusted-metadata rules apply. Scores and labels are display metadata, not
proof of audience size, quality, legality, or endorsement.

The proposal does not add user profiles or personalized rankings. A source
must document personalization outside ORSP and must not imply that a standard
ranking is personalized under the ORSP 1.5 contract.

## Implementation evidence

- The Dart reference source exposes weekly and monthly ranking resources.
- The OpenAPI 3.1 contract defines ranking collections, pages, and entries.
- The Rankings Profile conformance suite covers multiple definitions,
  category association, absolute ranks, pagination, snapshot continuity,
  invalid pagination, and an unknown ranking ID.

Independent source and reader implementations are still required before this
candidate can satisfy the governance acceptance gates for a stable release.
