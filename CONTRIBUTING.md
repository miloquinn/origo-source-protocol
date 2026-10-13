# Contributing

[简体中文](CONTRIBUTING.zh-CN.md)

Thank you for helping improve Open Reading Source Protocol.

Read [GOVERNANCE.md](GOVERNANCE.md) before proposing a protocol change. ORSP
optimizes for interoperability across independently developed readers and
sources, so a useful feature is not automatically suitable for the core.

## Implementation feedback

Implementation feedback is especially valuable. Please include:

1. whether you implemented a source, reader, adapter, registry, or test tool;
2. the language and framework used;
3. the protocol version and capabilities tested;
4. behavior that was ambiguous or differed between implementations;
5. a minimal request and response example where possible.

## Proposing a protocol change

Open a protocol issue describing:

1. the source-developer or reader problem;
2. why the current protocol or a namespaced extension cannot solve it;
3. the proposed request, response, and capability shape;
4. backward- and forward-compatibility impact;
5. security, privacy, accessibility, and copyright considerations;
6. migration and deprecation behavior;
7. implementation and test evidence.

Protocol changes must update the specification, OpenAPI document, relevant
JSON Schemas, examples, and conformance tests in the same pull request.

## Compatibility rules

- Minor releases may add optional fields and optional behavior only.
- Existing field and endpoint meanings cannot change within a major version.
- Implementations must ignore unknown JSON object members at every nesting
  level.
- Implementations must ignore unknown optional capability tokens.
- Extension capabilities use `reverse.domain:name` and cannot use the reserved
  `orsp` namespace.
- Missing and `null` are distinct; null is invalid unless explicitly declared.
- Incompatible changes require a new major protocol version and migration
  documentation.

## Local checks

The conformance reference toolchains are Dart 3.12.2 and Python 3.12. CI pins
these versions so formatter drift does not change acceptance between machines.

```bash
dart format --output=none --set-exit-if-changed \
  examples/dart_server.dart tool/conformance_test.dart
dart analyze examples/dart_server.dart tool/conformance_test.dart
dart run tool/conformance_test.dart
python -m pip install jsonschema pyyaml openapi-spec-validator
python scripts/validate_contracts.py
python scripts/validate_creator_extensions.py
python scripts/validate_chapter_updates.py
python scripts/validate_reading_profiles.py
python scripts/test_probe_source.py
dart run tool/discovery_conformance_test.dart
python scripts/registry_tool.py validate
python scripts/registry_tool.py build --check
python scripts/test_registry_tool.py
```

The CI workflow runs the same checks. JSON or YAML syntax validation alone is
not considered protocol conformance.

This repository does not accept source-listing submissions. The registry
schemas and tools are maintained only as a reference implementation for
independent communities; see [registry/README.md](registry/README.md).

By contributing, you agree that your contribution is licensed under the MIT
License used by this repository.

Chapter update extension checks: `python scripts/validate_chapter_updates.py`.
