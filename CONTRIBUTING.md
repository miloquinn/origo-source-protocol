# Contributing

Thank you for helping improve Open Reading Source Protocol.

## Proposing a protocol change

Open an issue describing:

1. the source-developer or reader problem;
2. why the current protocol cannot solve it;
3. the proposed request or response shape;
4. backward-compatibility impact;
5. security, privacy, and copyright considerations.

Protocol changes should update the specification, OpenAPI document, relevant
JSON Schemas, and at least one example.

## Compatibility

- Additive optional fields can usually remain within the current major version.
- Changing required fields, endpoint meaning, or response semantics requires a
  new major protocol version.
- Implementations must ignore unknown discovery fields unless a future
  capability explicitly says otherwise.

## Local checks

```bash
dart format --output=none --set-exit-if-changed examples/dart_server.dart
dart analyze examples/dart_server.dart
python -m json.tool schemas/discovery.schema.json > /dev/null
python -m json.tool examples/open-reading-source.json > /dev/null
```

By contributing, you agree that your contribution is licensed under the MIT
License used by this repository.
