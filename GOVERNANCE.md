# ORSP Governance

ORSP is developed as an open interoperability standard. The protocol belongs
to its implementers and users rather than to one reader, source, registry, or
company.

## Principles

1. **Interoperability before convenience.** A feature must behave consistently
   across common client and server languages.
2. **Small stable core.** Optional or experimental behavior begins as a
   namespaced extension instead of immediately expanding the core.
3. **Evidence before standardization.** Stable requirements come from working
   independent implementations and conformance tests.
4. **Safe readers.** ORSP data is untrusted; the protocol does not distribute
   executable scraping rules, credentials, or cookies to clients.
5. **Federation before gatekeeping.** Registries may be operated by many
   communities and must not redefine the wire protocol.
6. **Lawful distribution.** The protocol does not grant copyright or access
   rights, and governance must include practical reporting and removal paths.

## Normative sources

`SPECIFICATION.md` is the normative human-readable contract. The JSON Schemas,
OpenAPI document, and conformance suite are normative where they encode that
contract. If they conflict, the conflict is a protocol bug and must be fixed;
implementers should not silently choose one interpretation.

README files and translations are informative. A translation must identify the
protocol version it describes and must not introduce new requirements.

## Change process

Substantial protocol work uses an ORSP Enhancement Proposal (OEP) issue or
document with one of these states:

- **Problem:** use cases and interoperability evidence are being collected.
- **Draft:** a concrete contract and compatibility analysis exist.
- **Experimental:** the proposal has a namespaced capability and working code.
- **Candidate:** semantics are frozen and conformance tests exist.
- **Accepted:** the proposal is included in an ORSP release.
- **Deferred:** useful but not ready or not appropriate for the current scope.
- **Rejected:** incompatible with ORSP goals or superseded by another design.
- **Deprecated:** supported for migration but no longer recommended.

Repository maintainers seek public consensus and record the reason for a
decision. When consensus cannot be reached, maintainers may defer a proposal
rather than prematurely standardize competing behavior.

## Acceptance gates

A new stable core feature should have:

- at least two independent source implementations;
- at least two independent reader implementations;
- implementations spanning at least two programming-language ecosystems;
- machine-readable schemas where applicable;
- positive, negative, compatibility, and security conformance tests;
- documented fallback behavior for older clients;
- migration guidance and an ecosystem-impact summary.

An urgent security correction may be accepted before all gates are met, but the
exception and follow-up work must be documented.

## Releases and compatibility

Protocol releases use `MAJOR.MINOR`. A release candidate should be published
before a stable release so independent implementations can run the conformance
suite.

Within a major version, existing required behavior cannot be removed or
reinterpreted. Deprecation warnings may be introduced in a minor release, but
removal requires a new major version. Test-suite releases have their own build
or package version and do not change the wire protocol version.

## Security and conduct

Security vulnerabilities follow [SECURITY.md](SECURITY.md) and should not be
disclosed in public protocol issues before a fix is available. Participation
must remain technical, respectful, and welcoming to implementers from different
regions, languages, platforms, and project sizes.
