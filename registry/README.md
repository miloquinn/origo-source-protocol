# ORSP Registry Reference Format

[简体中文](README.zh-CN.md)

This directory is a non-official reference implementation of a federated ORSP
registry format. The Open Reading project does not operate an active source
directory, does not accept source-listing submissions, and does not distribute
`registry/generated/registry.json` to the official app.

Independent communities may reuse or fork these schemas and tools if they are
prepared to operate their own review, rights-reporting, security, and removal
process. Their registries are separate services and are not endorsed or
controlled by this project.

## Reference layout

```text
registry/sources/<source-id>.json
registry/status/<source-id>.json
registry/generated/registry.json
```

The filename must match the entry's `id`. The generated file is built from the
entries under `registry/sources/`; this repository intentionally keeps that
directory empty.

Reference fields include `discoveryUrl`, `maintainers`, `description`,
`languages`, `contentTypes`, `testQuery`, and an optional `reportingUrl`.
Protocol conformance does not prove content legality, quality, authorization,
or operator trustworthiness.

`registry/status/` may contain the latest bounded diagnostic record for a
source, validated by `schemas/source-status.schema.json`. It records a profile,
timestamp, stage outcomes, and bounded latency only. It MUST NOT contain reader
IP addresses, chapter text, cookies, credentials, private URLs, or browser
challenge material. A status file is registry metadata, never a replacement
for the source's own discovery document.

## Reference checks

```bash
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/registry_tool.py check-source path/to/source-entry.json
python scripts/registry_tool.py check-source path/to/source-entry.json --profile discovery
python scripts/registry_tool.py check-source path/to/source-entry.json --profile rankings
```

These tools validate format and network-safety invariants. They do not certify
content rights. An independent registry operator should adopt a review and
removal policy at least as strict as [POLICY.md](POLICY.md) and provide its own
public reporting channel.

See [SOURCE_POLICY.md](../SOURCE_POLICY.md) for the official project's source
distribution boundary.
