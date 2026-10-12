"""OEP-0004 structure and semantic fixtures; runs alongside existing core checks."""

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate_spec

ROOT = Path(__file__).resolve().parents[1]
schema = json.loads(
    (ROOT / "schemas/creator-extensions.schema.json").read_text(encoding="utf-8")
)


def validator(name):
    return Draft202012Validator(
        {**schema, "$ref": "#/$defs/" + name}, format_checker=FormatChecker()
    )


def check_anchor(anchor, text):
    """Text fixtures count Unicode scalars; never JS UTF-16 code units."""
    import hashlib

    validator("Anchor").validate(anchor)
    selector = anchor["selector"]
    assert selector["type"] == "TextPositionSelector"
    assert 0 <= selector["start"] < selector["end"] <= len(text)
    assert selector["quote"]["exact"] == text[selector["start"] : selector["end"]]
    assert anchor["contentVersion"] == hashlib.sha256(text.encode()).hexdigest()


def main():
    import hashlib

    Draft202012Validator.check_schema(schema)
    publication = {
        "id": "epub-1",
        "href": "https://creator.xxread.top/book.epub",
        "mediaType": "application/epub+zip",
        "bytes": 100,
        "sha256": "a" * 64,
    }
    validator("Publications").validate({"items": [publication]})
    for field, invalid in (
        ("href", "https://secret@host/a"),
        ("href", "javascript:alert(1)"),
        ("bytes", 0),
        ("sha256", "A" * 64),
        ("mediaType", "text/html"),
    ):
        changed = {**publication, field: invalid}
        assert not validator("Publication").is_valid(changed), field
    text = "第一句😀\n第二句"
    anchor = {
        "chapterId": "chapter-1",
        "contentVersion": hashlib.sha256(text.encode()).hexdigest(),
        "selector": {
            "type": "TextPositionSelector",
            "start": 3,
            "end": 4,
            "quote": {"exact": "😀", "prefix": "第一句", "suffix": "\n第二句"},
        },
    }
    check_anchor(anchor, text)
    for changed in ("range", "quote", "revision"):
        invalid = copy.deepcopy(anchor)
        if changed == "range":
            invalid["selector"]["end"] = 2
        if changed == "quote":
            invalid["selector"]["quote"]["exact"] = "不同"
        if changed == "revision":
            invalid["contentVersion"] = "b" * 64
        try:
            check_anchor(invalid, text)
        except AssertionError:
            pass
        else:
            raise AssertionError("Accepted invalid " + changed)
    comment = {
        "id": "comment-1",
        "bookId": "book-1",
        "author": {"id": "user-1", "displayName": "书友"},
        "body": "这一句让我停下来。",
        "createdAt": "2026-10-12T12:00:00Z",
        "anchor": anchor,
    }
    validator("Comments").validate({"items": [comment], "hasMore": False})
    assert not validator("Comments").is_valid({"items": [], "hasMore": True})
    assert not validator("CommentInput").is_valid(
        {"body": "text", "authorId": "forged"}
    )
    assert not validator("Comment").is_valid(
        {**comment, "author": {**comment["author"], "email": "private"}}
    )
    cfi = {
        "chapterId": "chapter-1",
        "contentVersion": "a" * 64,
        "selector": {
            "type": "EpubCfiSelector",
            "publicationId": "epub-1",
            "resource": "OPS/chapter.xhtml",
            "cfi": "epubcfi(/6/2!/4/2)",
        },
    }
    validator("Anchor").validate(cfi)
    for resource in ("../private", "/etc/a", "https://host/a"):
        invalid = copy.deepcopy(cfi)
        invalid["selector"]["resource"] = resource
        assert not validator("Anchor").is_valid(invalid)
    discovery_schema = json.loads(
        (ROOT / "schemas/discovery.schema.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (ROOT / "examples/yuanchuang-source.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(discovery_schema, format_checker=FormatChecker()).validate(
        manifest
    )
    api_path = ROOT / "extensions.openapi.yaml"
    api = yaml.safe_load(api_path.read_text(encoding="utf-8"))
    expected = json.loads(
        json.dumps(schema["$defs"]).replace("#/$defs/", "#/components/schemas/")
    )
    assert api["components"]["schemas"] == expected, (
        "Run scripts/build_creator_openapi.py"
    )
    validate_spec(api)
    print(
        "OEP-0004 validation passed: publications, Unicode anchors, CFI, privacy, pagination, OpenAPI"
    )


if __name__ == "__main__":
    main()
