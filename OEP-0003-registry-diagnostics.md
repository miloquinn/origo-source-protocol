# OEP-0003: Registry diagnostics and profile checks

Status: **Registry companion draft**

## Purpose

An imported source can publish syntactically valid ORSP discovery while an
adapter no longer produces readable search, discovery, catalog, or content
responses. Registry diagnostics report one bounded observation without adding
any field, endpoint, or capability to the ORSP wire protocol.

## Profiles

- `core-reading`: discovery, search, detail, catalog, and content complete for
  a registry-controlled stable test query.
- `discovery`: discovery, at least one non-empty curated section, a non-empty
  category list, and a category browse response containing at least one book.
- `rankings`: discovery, at least two ranking definitions, and a first ranking
  page containing a snapshot ID and a valid first-ranked book.

The Discovery Profile applies only when a source advertises all three optional
capabilities: `discover`, `categories`, and `browse`. A source can pass Core
Reading without implementing those optional capabilities.

The Rankings Profile applies only when a source advertises `rankings`. It is
independent of the Discovery Profile; a ranking uses `categories` only when its
definition includes `categoryId`.

## Record

Registry status records use
[`registry/schemas/source-status.schema.json`](registry/schemas/source-status.schema.json).
They contain only timestamps, profile, outcome, bounded stage latency, and
safe diagnostic messages. They MUST NOT contain chapter text, reader IPs,
cookies, credentials, private URLs, browser challenges, or stack traces.

`verified` means that profile passed at `checkedAt`; it is not a statement of
content rights, safety, quality, availability after that time, or source
operator identity. The source's discovery document remains the wire-protocol
source of truth.

## Compatibility

This proposal makes no ORSP wire change. Readers that do not use a
registry continue to interact only with discovery and standard API endpoints.
