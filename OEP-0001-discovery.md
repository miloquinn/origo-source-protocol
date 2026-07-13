# OEP-0001: Standard discovery and browsing

Status: **Candidate**  
Target: **ORSP 1.1**

## Problem

ORSP 1.0 lets a reader search only after the user already knows a title or
author. Independently implemented readers cannot offer interoperable featured
shelves, category navigation, or latest-update feeds without source-specific
extensions.

## Proposal

Reserve three optional standard capabilities and endpoint relations:

| Capability | Endpoint | Response |
| --- | --- | --- |
| `discover` | `GET v1/discover` | Curated sections containing book objects |
| `categories` | `GET v1/categories` | Stable category IDs and display names |
| `browse` | `GET v1/browse` | Search-style pagination by category or sort |

The standardized browse sorts are `latest` and `popular`. Sources may implement
any optional capability independently except that `categories` requires
`browse`, because category IDs are defined as browse inputs.

## Compatibility

- The four ORSP 1.0 core endpoints and object meanings are unchanged.
- Existing 1.0 sources remain conforming core sources and require no changes.
- Existing 1.x clients already ignore unknown capability tokens.
- A client exposes discovery UI only after the corresponding capability is
  advertised; otherwise it falls back to core search.
- All new response objects use existing book metadata and forward-compatible
  unknown-member handling.

## Security and privacy

The new endpoints are unauthenticated, safe, idempotent `GET` operations under
the same response-size, redirect, caching, SSRF, and untrusted-input rules as
the core profile. ORSP 1.1 does not define personal profiles or personalized
recommendations. Sources must not imply that a curated section is personalized
unless that behavior is documented outside the protocol.

## Implementation evidence

- The Open Reading Flutter client implements capability-gated discovery with
  fallback to core search.
- This repository's Dart reference source implements all three capabilities.
- The conformance suite covers positive discovery/category/browse flows and
  invalid browse sort behavior.

Independent source and reader implementations are still required before the
candidate can be declared a stable release under the governance acceptance
gates.
