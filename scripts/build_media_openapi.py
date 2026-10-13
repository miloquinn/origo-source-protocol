"""Build OEP-0006 OpenAPI components from the canonical media JSON Schema."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "HttpUrl": "MediaHttpUrl",
    "Headers": "MediaHeaders",
    "Image": "MediaImage",
    "Audio": "MediaAudio",
    "ImageContent": "ImageChapterContent",
    "AudioContent": "AudioChapterContent",
}


def components():
    definitions = json.loads(
        (ROOT / "schemas/media-reading.schema.json").read_text(encoding="utf-8")
    )["$defs"]
    result = {}
    for name, definition in definitions.items():
        encoded = json.dumps(definition)
        for old, new in NAMES.items():
            encoded = encoded.replace(f'#/$defs/{old}"', f'#/components/schemas/{new}"')
        result[NAMES[name]] = json.loads(encoded)
    return result


def main():
    path = ROOT / "openapi.yaml"
    api = yaml.safe_load(path.read_text(encoding="utf-8"))
    schemas = api["components"]["schemas"]
    if "TextChapterContent" not in schemas:
        schemas["TextChapterContent"] = schemas["ChapterContent"]
    schemas.update(components())
    schemas["ChapterContent"] = {
        "description": "Core text, or explicitly advertised OEP-0006 media representations.",
        "oneOf": [
            {"$ref": "#/components/schemas/" + name}
            for name in (
                "TextChapterContent",
                "ImageChapterContent",
                "AudioChapterContent",
            )
        ],
    }
    schemas["Book"]["properties"].update(
        mediaKind={
            "type": "string",
            "minLength": 1,
            "maxLength": 64,
            "description": "Known values: text, image-sequence, remote-audio, unknown. Unrecognized values map to unknown.",
        },
        type={
            "type": "integer",
            "description": "Optional legacy reader bridge: text 8, image sequence 64, remote audio 32.",
        },
    )
    api["info"]["description"] = (
        "ORSP 1.6 candidate: Core Reading, Discovery and Rankings, "
        "with optional OEP-0006 image/audio representations. "
        "EPUB and chapter updates have separate companion OpenAPI documents."
    )
    path.write_text(
        yaml.safe_dump(api, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
