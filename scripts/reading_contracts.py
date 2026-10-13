"""Shared schema access for profile checks and the read-only source probe."""

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MEDIA_CAPABILITIES = {
    "image/sequence": "top.xxread:image-sequence",
    "audio/uri": "top.xxread:remote-audio",
}


def media_issues(manifest, content):
    issues = []
    content_type = content.get("contentType")
    required = (
        MEDIA_CAPABILITIES.get(content_type) if isinstance(content_type, str) else None
    )
    if required and required not in manifest["capabilities"]:
        issues.append("Media representation was not advertised as a capability")
    if manifest.get("contentTypes") and content_type not in manifest["contentTypes"]:
        issues.append("Returned contentType is absent from declared contentTypes")
    return issues


def strict_json(data):
    def invalid_constant(_value):
        raise ValueError("Non-finite numbers are not JSON")

    return json.loads(data, parse_constant=invalid_constant)


class Contracts:
    def __init__(self):
        self.api = yaml.safe_load((ROOT / "openapi.yaml").read_text(encoding="utf-8"))
        self.roots = {"core": {"components": self.api["components"]}}
        for label, filename in (
            ("discovery", "discovery.schema.json"),
            ("media", "media-reading.schema.json"),
            ("publications", "creator-extensions.schema.json"),
            ("updates", "chapter-updates.schema.json"),
        ):
            schema = strict_json(
                (ROOT / "schemas" / filename).read_text(encoding="utf-8")
            )
            Draft202012Validator.check_schema(schema)
            self.roots[label] = schema

    def validator(self, profile, name=None):
        schema = self.roots[profile]
        if name:
            prefix = "#/components/schemas/" if profile == "core" else "#/$defs/"
            schema = {**schema, "$ref": prefix + name}
        return Draft202012Validator(schema, format_checker=FormatChecker())

    def issues(self, profile, name, value):
        # Never serialize the rejected instance: it may include a chapter body.
        return [
            f"{'.'.join(map(str, error.path)) or '<root>'}: {error.validator} constraint failed"
            for error in self.validator(profile, name).iter_errors(value)
        ]
