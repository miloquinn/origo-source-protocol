"""OEP-0005 Schema/OpenAPI and live HTTP mutation conformance checks."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate_spec

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from chapter_updates_server import BOOK_ID, CAPABILITY, ChapterUpdateSource  # noqa: E402


def main():
    schema = json.loads(
        (ROOT / "schemas/chapter-updates.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    validators = {
        name: Draft202012Validator(
            {**schema, "$ref": "#/$defs/" + name}, format_checker=FormatChecker()
        )
        for name in schema["$defs"]
    }
    api = yaml.safe_load(
        (ROOT / "chapter-updates.openapi.yaml").read_text(encoding="utf-8")
    )
    expected = json.loads(
        json.dumps(schema["$defs"]).replace("#/$defs/", "#/components/schemas/")
    )
    assert api["components"]["schemas"] == expected, "Rebuild chapter update OpenAPI"
    validate_spec(api)
    source = ChapterUpdateSource()
    source.publish("chapter-1", "First chapter", "Original text 😀", 0)
    base = source.start()
    path = f"/api/v1/books/{BOOK_ID}"
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    def get(relative, *, headers=None, status=200, profile=None):
        try:
            response = urlopen(
                Request(base + relative, headers=headers or {}), timeout=5
            )
        except HTTPError as error:
            response = error
        with response:
            check(
                response.status == status,
                f"Expected {status} for {relative}; got {response.status}",
            )
            data = response.read()
            body = json.loads(data) if data else None
            if profile:
                validators[profile].validate(body)
            if status == 304:
                check(not data, "304 must have no body")
            return body, response.headers

    try:
        discovery, _ = get("/.well-known/open-reading-source.json")
        check(CAPABILITY in discovery["capabilities"], "Advertised capability")
        discovery_schema = json.loads(
            (ROOT / "schemas/discovery.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator(discovery_schema, format_checker=FormatChecker()).validate(
            discovery
        )
        first, first_headers = get(path + "/updates", profile="UpdateState")
        check(first["chapterCount"] == 1, "Initial baseline is one chapter")
        get(
            path + "/updates",
            headers={"If-None-Match": first_headers["ETag"]},
            status=304,
        )
        get(
            path + "/updates",
            headers={"If-None-Match": '"other",W/' + first_headers["ETag"]},
            status=304,
        )
        timestamp = first["updatedAt"]
        source.publish(
            "chapter-2", "Second chapter", "New text", 2, updated_at=timestamp
        )
        second, _ = get(
            path + "/updates",
            headers={"If-None-Match": first_headers["ETag"]},
            profile="UpdateState",
        )
        check(
            second["catalogVersion"] != first["catalogVersion"],
            "Append changes catalog version even with equal timestamp",
        )
        check(
            second["chapterCount"] == 2
            and second["latestChapter"]["id"] == "chapter-2",
            "Append updates count and latest",
        )
        legacy, _ = get(path + "/chapters", profile="Catalog")
        check(
            [x["id"] for x in legacy["items"]] == ["chapter-1", "chapter-2"],
            "Legacy catalog sees new chapter without new parameters",
        )
        old_text_version = legacy["items"][0]["contentVersion"]
        source.revise("chapter-1", content="Corrected text 😀", updated_at=timestamp)
        corrected, _ = get(path + "/updates", profile="UpdateState")
        check(
            corrected["catalogVersion"] != second["catalogVersion"]
            and corrected["chapterCount"] == 2,
            "Same count correction changes version",
        )
        version = corrected["catalogVersion"]
        catalog, _ = get(
            path + f"/chapters?catalogVersion={version}", profile="Catalog"
        )
        check(
            catalog["items"][0]["contentVersion"] != old_text_version,
            "Correction invalidates exactly the changed text",
        )
        check(
            catalog["items"][1]["contentVersion"]
            == legacy["items"][1]["contentVersion"],
            "Unchanged chapter remains reusable",
        )
        chapter, _ = get(
            path + f"/chapters/chapter-1?catalogVersion={version}", profile="Content"
        )
        check(
            chapter["contentVersion"]
            == hashlib.sha256(chapter["content"].encode()).hexdigest(),
            "Content version hashes exact UTF-8",
        )
        first_page, page_headers = get(
            path + f"/chapters?pageSize=1&catalogVersion={version}", profile="Catalog"
        )
        source.publish("chapter-middle", "Middle insertion", "Middle text", 1)
        conflict, _ = get(
            path + f"/chapters?page=2&pageSize=1&catalogVersion={version}", status=409
        )
        check(
            conflict["error"]["code"] == "X_CATALOG_VERSION_CONFLICT",
            "Pagination rejects mixed versions",
        )
        get(
            path + f"/chapters?pageSize=1&catalogVersion={version}",
            headers={"If-None-Match": page_headers["ETag"]},
            status=409,
        )
        get(path + f"/chapters/chapter-1?catalogVersion={version}", status=409)
        inserted, _ = get(path + "/chapters", profile="Catalog")
        check(
            [x["id"] for x in inserted["items"]]
            == ["chapter-1", "chapter-middle", "chapter-2"],
            "Middle insertion preserves original identities",
        )
        source.revise("chapter-1", title="Renamed chapter", order=3)
        reordered, _ = get(path + "/updates", profile="UpdateState")
        check(
            reordered["latestChapter"]["id"] == "chapter-1",
            "Reordering uses stable ID and new order",
        )
        source.withdraw("chapter-middle")
        withdrawn, _ = get(path + "/chapters", profile="Catalog")
        check(
            {x["id"] for x in withdrawn["items"]} == {"chapter-1", "chapter-2"},
            "Withdrawal removes only that logical chapter",
        )
        try:
            source.publish("chapter-middle", "Different resource", "bad", 0)
        except ValueError:
            check(True, "Withdrawn identity not reused")
        else:
            check(False, "Identity was reused")
        state, _ = get(path + "/updates", profile="UpdateState")
        page1, headers1 = get(
            path + f"/chapters?pageSize=1&catalogVersion={state['catalogVersion']}",
            profile="Catalog",
        )
        page2, headers2 = get(
            path
            + f"/chapters?page=2&pageSize=1&catalogVersion={state['catalogVersion']}",
            profile="Catalog",
        )
        check(
            page1["catalogVersion"] == page2["catalogVersion"],
            "Two pages share catalog version",
        )
        check(
            headers1["ETag"] != headers2["ETag"],
            "Per-page ETags differ without a mixed catalog",
        )
        for query in (
            "catalogVersion=",
            "catalogVersion=bad%2Ftoken",
            "page=0",
            "pageSize=1001",
        ):
            invalid, _ = get(path + "/chapters?" + query, status=400)
            check(
                invalid["error"]["code"] == "INVALID_PARAMETER",
                "Invalid parameter envelope",
            )
        get("/api/v1/books/missing/updates", status=404)
        get(path + "/chapters/missing", status=404)
        get("/api/v1/search?q=Original")
        get(path)
        source.withdraw("chapter-1")
        source.withdraw("chapter-2")
        empty, _ = get(path + "/updates", profile="UpdateState")
        check(
            empty["chapterCount"] == 0 and "latestChapter" not in empty,
            "No fake latest chapter for empty catalog",
        )
        check(
            not validators["UpdateState"].is_valid(
                {**empty, "latestChapter": legacy["items"][0]}
            ),
            "Zero count forbids latest",
        )
        check(
            not validators["Content"].is_valid({**chapter, "contentVersion": "bad"}),
            "Invalid content hash rejected",
        )
        print(
            f"Chapter update conformance passed: {checks} checks; Schema/OpenAPI validated"
        )
    finally:
        source.close()


if __name__ == "__main__":
    main()
