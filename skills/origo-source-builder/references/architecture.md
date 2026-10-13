# A small source that can grow

Keep four responsibilities distinct: storage supplies a coherent book snapshot;
the service shapes that snapshot into ORSP; HTTP validates inputs and validators;
the reader decides rendering and persists canonical reading positions. The
starter uses `library.py` and `server.py` to keep storage separate from delivery.

The file adapter caches parsed content until the file stat changes. Each request
uses one captured snapshot; never read page metadata and chapter content from
different database transactions. Use atomic replacement when rewriting the file.
The 8 MiB file limit is a starter resource limit; large libraries should replace
the adapter with indexed database queries rather than raise it indefinitely.

Keep metadata, chapter bodies and binary assets separate when adopting a database
and object storage. Store durable asset keys and revision metadata; delivery URLs
can change without changing book/chapter identity. Text bodies, ordered image
resources and recordings have distinct content-version semantics. ETag validates
one representation, catalogVersion validates a whole catalog snapshot.

Use bounded page sizes, cached projections and explicit invalidation. Adding
workers, queues or extra servers should solve measured demand. Replacing the file
adapter with PostgreSQL or an upstream adapter should not alter the public wire
contract. An authorized upstream adapter may translate data; do not transfer its
executable rules or credentials to the reader.

The starter listens on loopback. For a requested HTTPS deployment, put it behind
a reverse proxy and set `--public-origin https://books.example.org`; this ensures
discovery advertises the public origin, not 127.0.0.1. Do not derive the public
origin from an untrusted Host or forwarded header. Move configuration/content
outside immutable application releases, back up content, and keep secrets out
of exported samples. The starter has no public write or login endpoints.

Origo Source / 元源 are human names. ORSP's existing JSON discriminator,
well-known path, capability tokens and endpoint relations remain intact.
New capabilities are optional profiles with fallback and conformance checks;
account authentication, payments and reading synchronization have separate APIs.

## HTTP and HTTPS delivery

Public sources should expose `https://books.example.org/.well-known/origo-source.json`.
Behind a TLS reverse proxy, run `python server.py --public-origin https://books.example.org`
and keep the upstream on loopback. For direct TLS, use
`python server.py --tls-cert /secure/fullchain.pem --tls-key /secure/private.pem`;
both options are required together. The listener then advertises an HTTPS API
origin and requires TLS 1.2 or later. Supply `--public-origin` with the actual
public hostname when exposing it externally. Provision certificates through your
hosting provider; never export production keys in this Skill or source repository.
The certificate-generating validation test uses an ephemeral local certificate.
Clients keep hostname and trust verification enabled. HTTP is supported for local
development and explicit existing sources; it is never an automatic TLS fallback.
The legacy discovery alias returns the old protocol identifier for installed readers.
