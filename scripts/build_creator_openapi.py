"""Generate standalone OEP-0004 OpenAPI components from the canonical JSON Schema."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "extensions.openapi.yaml"
    api = yaml.safe_load(path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "schemas/creator-extensions.schema.json").read_text(encoding="utf-8")
    )
    api["components"]["schemas"] = json.loads(
        json.dumps(schema["$defs"]).replace("#/$defs/", "#/components/schemas/")
    )
    api = json.loads(
        json.dumps(api).replace(
            "./schemas/creator-extensions.schema.json#/$defs/", "#/components/schemas/"
        )
    )
    path.write_text(
        yaml.safe_dump(api, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
