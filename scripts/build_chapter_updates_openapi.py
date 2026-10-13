"""Rebuild standalone OEP-0005 OpenAPI components from its canonical schema."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "chapter-updates.openapi.yaml"
    api = yaml.safe_load(path.read_text(encoding="utf-8"))
    definitions = json.loads(
        (ROOT / "schemas/chapter-updates.schema.json").read_text(encoding="utf-8")
    )["$defs"]
    api["components"]["schemas"] = json.loads(
        json.dumps(definitions).replace("#/$defs/", "#/components/schemas/")
    )
    path.write_text(yaml.safe_dump(api, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    main()
