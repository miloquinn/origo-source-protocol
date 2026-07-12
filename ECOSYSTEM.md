# ORSP Ecosystem Architecture

ORSP separates three concerns so the community can grow without making readers
unsafe or the wire protocol unstable.

## 1. Wire protocol

The ORSP core is the HTTP contract implemented by readers and sources. It
defines data and behavior, not scraping programs. A reader should be able to
connect to any conforming source without source-specific code.

## 2. Server-side adapters

An adapter translates an existing authorized content service into ORSP. It may
use HTML parsing, vendor APIs, databases, or other source-specific logic on the
server side. Credentials and executable rules remain under the adapter
operator's control and are never sent to readers.

Future adapter SDKs should provide:

- typed ORSP response models;
- request validation and pagination helpers;
- caching, rate limiting, and safe upstream-fetch defaults;
- HTML sanitization utilities;
- conformance-test integration;
- migration guides for existing book-source formats.

Adapter compatibility is separate from the ORSP wire version. A legacy format
can evolve or disappear without forcing every reader to change.

## 3. Federated registries

A registry helps users discover sources. It is not the protocol authority and
does not need to be unique. Readers may subscribe to multiple community,
regional, organizational, or private registries.

A future registry companion specification should describe signed or
integrity-protected entries containing at least:

- source ID and discovery URL;
- operator and maintainer information;
- supported languages and capabilities;
- last successful conformance result and test-suite version;
- health-check time without exposing private infrastructure;
- content-rights declaration, reporting contact, and removal status;
- optional reputation and community moderation metadata.

Registry entries must not duplicate the complete discovery document as a new
source of truth. Readers should fetch discovery from the source and compare the
stable source ID.

This repository now contains an initial PR-based implementation under
[`registry/`](registry/README.md). It is intentionally a community registry
prototype rather than the final companion specification. Operational evidence
from this implementation should guide the federated format.

## Trust model

Protocol conformance proves interoperability, not legality, content quality, or
operator trustworthiness. Registries should present these as separate signals.
A source can be technically conforming and still be unsuitable for a registry.

Readers should clearly show source identity, origin, permissions, security
warnings, and removal information. Private-network sources should require an
explicit client policy.

## Roadmap

1. Stabilize ORSP 1.0 and publish a reusable core conformance kit.
2. Build adapter SDKs in at least two server ecosystems.
3. Test multiple independent readers and sources and publish a compatibility
   matrix.
4. Draft a federated registry companion specification using real operational
   experience.
5. Standardize additional capabilities only after extension implementations
   demonstrate compatible semantics.
