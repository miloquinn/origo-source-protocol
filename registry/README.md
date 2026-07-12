# ORSP Community Source Registry

This directory is the initial community registry for public ORSP sources. It is
a discovery and moderation layer, not a replacement for the ORSP wire protocol.

Each source is submitted as one JSON file:

```text
registry/sources/<source-id>.json
```

The filename MUST exactly match the entry's `id`. Do not edit
`registry/generated/registry.json` by hand; it is built from accepted entries.

## Submit a source

1. Fork the repository.
2. Copy `registry/examples/source-entry.json` to
   `registry/sources/<your-source-id>.json`.
3. Replace every example value and choose a stable `testQuery` that returns at
   least one book with at least one chapter.
4. Run the local checks below.
5. Open a pull request using `.github/PULL_REQUEST_TEMPLATE/source-submission.md`.

The discovery document's `id` MUST match both the registry entry and filename.
All four ORSP Core Reading capabilities are required.

## What registry fields mean

- `discoveryUrl`: canonical HTTPS discovery-document URL.
- `maintainers`: GitHub accounts responsible for the source entry.
- `description`: registry-facing summary; runtime source metadata still comes
  from discovery.
- `languages`: claimed content languages. Network verification compares these
  with discovery but discovery remains the runtime source of truth.
- `contentTypes`: operator declaration of the basis for distribution.
- `testQuery`: stable query used only for compatibility and health checks.
- `reportingUrl`: optional abuse, copyright, or availability reporting page.

Protocol conformance does not prove content legality, quality, or operator
trustworthiness. Those are separate registry and community decisions.

## Local checks

```bash
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/registry_tool.py check-source \
  registry/sources/<source-id>.json
```

The first two commands are safe static checks and run on every pull request.
For submitted manifests, a separate workflow runs the already-reviewed
validator from the pull request's base revision; it does not execute submitted
code or expose repository credentials. The network check rejects private,
loopback, link-local, multicast, and reserved IP addresses, pins the connection
to a validated address, and repeats validation after every redirect.

## Review and publication

A pull request is eligible for merge when:

- the manifest and filename pass static validation;
- source and discovery IDs match;
- discovery and API URLs pass public-network safety checks;
- search, detail, catalog, and content complete successfully;
- the submitter completes the authorization and maintenance declarations;
- no unresolved security, abuse, or copyright concern remains.

Accepted entries are sorted by source ID in
`registry/generated/registry.json`. Reader applications may consume that file,
but MUST fetch current discovery metadata directly from each source before use.

## Health and removal

Automated checks produce operational reports separately from author-controlled
source entries. A single failure does not remove a source.

Suggested operational states are `verified`, `degraded`, `offline`,
`unmaintained`, `suspended`, and `removed`. Maintainers may suspend a source
immediately for a credible security or legal risk. Removed entries are retained
under `registry/removed/` with a public reason when disclosure is appropriate.

See [POLICY.md](POLICY.md) for review, transfer, suspension, and removal rules.
