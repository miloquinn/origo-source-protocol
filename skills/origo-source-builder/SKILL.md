---
name: origo-source-builder
description: "Create or extend an independent Origo Source (元源) service compatible with ORSP. Use for book/chapter sources, chapter updates, EPUB publications, image or recorded-audio chapters, and rankings; includes a runnable starter and canonical contract checks."
---

# Origo Source 元源搭建

Build a working source using the user's content and preferred stack. Origo Source
is the public name; ORSP is the protocol. Keep `protocol: open-reading-source`,
the well-known filename, existing `v1/...` relations, headers and source IDs.
The bundled contract is ORSP 1.6 **candidate**, not a stable release.

## Start with the actual project

If the user has a service, inspect its data and routes and add an adapter at that
boundary. Do not replace their stack, accounts, storage or repository layout.
For a new source, use the bundled zero-dependency Python starter when suitable:

```bash
python "/path/to/origo-source-builder/scripts/create_source.py" ./my-source --id org.example.library --name "My library"
cd my-source
python server.py --port 8787
```

Run from the user’s chosen code workspace and replace /path/to/origo-source-builder
with this Skill’s actual path. Keep generated projects outside the installed Skill
and protocol repository. In the generated project,
`library.json` holds original sample content; replace it with the user's books
without changing already-published book/chapter IDs. The starter implements
core reading, browse and chapter updates. Other profiles require implementation
before advertisement. It is a small file-backed source, not a publishing CMS.

Read [architecture.md](references/architecture.md) when deciding data ownership,
cache behavior or deployment. Read `references/orsp/SPECIFICATION.md` for the
core and only the relevant OEP when adding a profile:

- OEP-0004: full EPUB publications; work/paragraph comments remain a separate draft.
- OEP-0005: additions, corrections, deletion/reordering, catalog version pinning.
- OEP-0006: images, recorded audio, expiration and public request hints.
- OEP-0007: multiple named rankings and pagination snapshots.

These `references/orsp/` files are included in the downloadable bundle from
the canonical protocol repository. Never invent a second field contract.

## Interoperability that matters

Implement discovery, search, detail, catalog and content together. Match requested
book/chapter IDs in responses; include title in content. Retain text endpoints
when offering EPUB. Source/book/chapter identity is distinct from URLs and pages.
Declare only working optional capabilities. Ignore unfamiliar JSON metadata,
but explicitly reject unsupported operational content types.

For updates, invalidate snapshots on body edits as well as additions; chapter
count alone is insufficient. OEP-0005 text versions hash exact UTF-8 content;
media revisions and publication file checksums have separate semantics. Reject
stale catalogVersion with 409 before considering conditional 304 responses.
Image/audio delivery must not expose cookies, credentials or a reader's session.

Keep source adaptation server-side and operate on the user's authorized content.
Public core reading is independent of Origo Account, purchases and reader sync.
Prepare deployment files for the requested target; execute external deployment
only when the user's request covers it. Do not assume creating a project also
authorizes changing DNS, another person's source or their production data.

## Validate the result

Install tooling from `contract/requirements.txt` in the generated project.
Start the actual generated service and run:

```bash
python -m pip install -r contract/requirements.txt
python contract/scripts/probe_source.py http://127.0.0.1:8787/.well-known/open-reading-source.json --allow-loopback
```

The probe samples one book/chapter and does not download assets. Also exercise
the user's requested profiles with real HTTP: edit a chapter without changing
count, test stale pagination/304, verify actual EPUB bytes/hash and media URLs,
and compare ranking snapshots across pages as appropriate. The bundled reference
suites verify the **contract fixtures**, not the generated or user's server;
do not report those passes as acceptance of their implementation.

Deliver the project, run commands, verified discovery URL, declared capabilities
and remaining client/deployment limits. Do not claim a service is public or
physical playback works solely because JSON parsing passed.
