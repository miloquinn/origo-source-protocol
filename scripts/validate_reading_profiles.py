"""Validate complete reading contracts using original fixtures and real HTTP."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import wave
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zipfile import ZipFile

from build_media_openapi import components
from openapi_spec_validator import validate_spec
from probe_source import ProbeError, Transport, probe
from reading_contracts import Contracts, strict_json
from registry_tool import RegistryError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from reading_profiles_server import ReadingProfileSource, epub


def main():
    contracts = Contracts()
    validate_spec(contracts.api)
    for name, expected in components().items():
        assert contracts.api["components"]["schemas"][name] == expected, (
            "Rebuild media OpenAPI"
        )
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    def valid(profile, model, body):
        contracts.validator(profile, model).validate(body)
        check(True, f"Valid {profile}/{model}")

    def invalid(profile, model, body, message):
        check(not contracts.validator(profile, model).is_valid(body), message)

    source = ReadingProfileSource()
    base = source.start()

    def get(
        path, *, status=200, headers=None, model=None, profile="core", binary=False
    ):
        url = path if path.startswith("http") else base + path
        try:
            response = urlopen(Request(url, headers=headers or {}), timeout=5)
        except HTTPError as error:
            response = error
        with response:
            check(response.status == status, f"HTTP status for {path}")
            data = response.read()
            if status == 304:
                check(not data, "304 body is empty")
                return None, response.headers
            body = data if binary else strict_json(data.decode("utf-8"))
            if model:
                valid(profile, model, body)
            return body, response.headers

    try:
        manifest, _ = get("/.well-known/open-reading-source.json")
        valid("discovery", None, manifest)
        for capability, content_type in (
            ("top.xxread:image-sequence", "image/sequence"),
            ("top.xxread:remote-audio", "audio/uri"),
        ):
            missing = copy.deepcopy(manifest)
            missing.pop("contentTypes")
            invalid("discovery", None, missing, f"{capability} requires contentTypes")
            missing = copy.deepcopy(manifest)
            missing["contentTypes"].remove(content_type)
            invalid(
                "discovery", None, missing, "Advertised media requires its content type"
            )
            missing = copy.deepcopy(manifest)
            missing["capabilities"].remove(capability)
            invalid(
                "discovery",
                None,
                missing,
                "Media type requires corresponding capability",
            )
        old = copy.deepcopy(manifest)
        old.update(
            protocolVersion="1.1",
            capabilities=[
                "search",
                "detail",
                "catalog",
                "content",
                "org.example:future",
            ],
        )
        old.pop("contentTypes")
        valid("discovery", None, old)
        valid(
            "core",
            "Book",
            {"id": "future-book", "title": "Future", "mediaKind": "org.example:future"},
        )
        get("/api/v1/categories", model="CategoryPage")
        get("/api/v1/discover", model="DiscoveryPage")
        get("/api/v1/search?q=Original&pageSize=2", model="SearchPage")
        get("/api/v1/browse?category=text&sort=latest&pageSize=2", model="SearchPage")
        for book_id in source.books:
            path = "/api/v1/books/" + book_id
            detail, _ = get(path, model="Book")
            state, _ = get(path + "/updates", profile="updates", model="UpdateState")
            catalog, _ = get(
                path + "/chapters?catalogVersion=" + state["catalogVersion"],
                profile="updates",
                model="Catalog",
            )
            check(catalog["pageSize"] == 100, "Core catalog page size default")
            check(
                len(catalog["items"]) == state["chapterCount"],
                "Directory and update count agree",
            )
            chapter_id = catalog["items"][0]["id"]
            chapter, _ = get(path + "/chapters/" + chapter_id, model="ChapterContent")
            check(
                chapter["bookId"] == book_id and chapter["chapterId"] == chapter_id,
                "Stable resource identities",
            )
            check(
                chapter["contentVersion"] == catalog["items"][0]["contentVersion"],
                "Revision matches directory",
            )
            if detail["mediaKind"] == "image-sequence":
                check(detail["type"] == 64, "Image reader bridge")
                image_chapter = chapter
                for image in chapter["images"]:
                    pixels, headers = get(image["url"], binary=True)
                    check(
                        pixels.startswith(b"\x89PNG\r\n\x1a\n")
                        and headers["Content-Type"] == "image/png",
                        "Real PNG asset",
                    )
                check(
                    chapter["images"][0]["url"] != chapter["images"][1]["url"],
                    "Ordered image assets",
                )
            elif detail["mediaKind"] == "remote-audio":
                check(detail["type"] == 32, "Audio reader bridge")
                first_audio = chapter
                get(chapter["audio"]["url"], status=403, model="ErrorResponse")
                refreshed, _ = get(
                    path + "/chapters/" + chapter_id, model="ChapterContent"
                )
                check(
                    refreshed["audio"]["url"] != chapter["audio"]["url"],
                    "One chapter refresh rotates expired lease",
                )
                check(
                    refreshed["contentVersion"] == chapter["contentVersion"],
                    "Lease rotation preserves logical revision",
                )
                audio, _ = get(refreshed["audio"]["url"], binary=True)
                with wave.open(io.BytesIO(audio)) as recording:
                    check(
                        recording.getnframes() / recording.getframerate()
                        == refreshed["audio"]["durationSeconds"],
                        "Playable WAV duration",
                    )
                partial, headers = get(
                    refreshed["audio"]["url"],
                    status=206,
                    binary=True,
                    headers={"Range": "bytes=0-15"},
                )
                check(
                    partial == audio[:16]
                    and headers["Content-Range"] == f"bytes 0-15/{len(audio)}",
                    "Audio byte range",
                )
            elif chapter["contentType"] == "text/markdown":
                check("![" in chapter["content"], "Illustrated Markdown")
                data, _ = get(urljoin(chapter["baseUrl"], "page-1.png"), binary=True)
                check(
                    data.startswith(b"\x89PNG"),
                    "Relative Markdown image resolves using baseUrl",
                )
        for model, body, field in (
            ("ImageContent", image_chapter, "images"),
            ("AudioContent", first_audio, "audio"),
        ):
            valid("media", model, body)
            missing = copy.deepcopy(body)
            missing.pop(field)
            invalid("media", model, missing, "Missing media asset")
            mixed = copy.deepcopy(body)
            mixed["audio" if field == "images" else "images"] = (
                {} if field == "images" else []
            )
            invalid("media", model, mixed, "Mixed representations are rejected")
            invalid(
                "media",
                model,
                {**body, "content": "not empty"},
                "Media content must be empty",
            )
        invalid(
            "media",
            "ImageContent",
            {**image_chapter, "images": []},
            "No empty image sequence",
        )
        for url in (
            "file:///etc/private",
            "javascript:alert(1)",
            "https://user:secret@example.org/a",
            "https://example.org/\r\nheader",
        ):
            invalid("media", "Audio", {"url": url}, "Unsafe media URL")
        for headers in (
            {"Cookie": "session"},
            {"Authorization": "token"},
            {"Accept": "audio/wav\r\nCookie: token"},
        ):
            invalid(
                "media",
                "Audio",
                {"url": "https://example.org/a", "headers": headers},
                "Private or injected headers rejected",
            )
        valid(
            "media",
            "Audio",
            {
                "url": "https://example.org/a",
                "headers": {"Accept": "audio/wav", "Origin": "https://example.org"},
                "transport": "hls",
            },
        )
        for duration in (0, -1, float("inf")):
            invalid(
                "media",
                "Audio",
                {"url": "https://example.org/a", "durationSeconds": duration},
                "Nonpositive/nonfinite duration",
            )
        try:
            strict_json('{"durationSeconds":NaN}')
        except ValueError:
            check(True, "Non-JSON NaN is rejected")
        else:
            raise AssertionError("Accepted NaN")
        check(epub() == epub(), "Immutable sample EPUB is deterministic")
        publications, _ = get(
            "/api/v1/books/epub-book/publications",
            profile="publications",
            model="Publications",
        )
        publication = publications["items"][0]
        data, headers = get(publication["href"], binary=True)
        check(
            len(data) == publication["bytes"]
            and hashlib.sha256(data).hexdigest() == publication["sha256"],
            "EPUB size and integrity",
        )
        check(
            headers["Content-Type"] == "application/epub+zip", "Publication media type"
        )
        with ZipFile(io.BytesIO(data)) as archive:
            check(
                archive.namelist()[0] == "mimetype"
                and archive.read("mimetype") == b"application/epub+zip",
                "EPUB package structure",
            )
            check(
                "OPS/package.opf" in archive.namelist()
                and "OPS/nav.xhtml" in archive.namelist(),
                "EPUB package and navigation",
            )
        partial, _ = get(
            publication["href"],
            status=206,
            binary=True,
            headers={"Range": "bytes=0-31"},
        )
        check(partial == data[:32], "Publication supports range download")
        tail, tail_headers = get(
            publication["href"], status=206, binary=True, headers={"Range": "bytes=-16"}
        )
        check(
            tail == data[-16:] and tail_headers["ETag"] == headers["ETag"],
            "Ranges retain full representation ETag",
        )
        get(
            publication["href"],
            status=304,
            headers={"Range": "bytes=0-31", "If-None-Match": headers["ETag"]},
        )
        full, _ = get(
            publication["href"],
            binary=True,
            headers={"Range": "bytes=0-31", "If-Range": '"obsolete"'},
        )
        check(full == data, "Changed If-Range validator sends complete file")
        get(
            publication["href"],
            status=416,
            headers={"Range": "bytes=999999999-"},
            model="ErrorResponse",
        )
        path = "/api/v1/books/text-book"
        before, headers = get(path + "/updates", profile="updates", model="UpdateState")
        get(path + "/updates", status=304, headers={"If-None-Match": headers["ETag"]})
        source.revise_text("Corrected original text, with the same chapter count.")
        after, _ = get(path + "/updates", profile="updates", model="UpdateState")
        check(
            before["chapterCount"] == after["chapterCount"]
            and before["updatedAt"] == after["updatedAt"],
            "Same count and timestamp correction fixture",
        )
        check(
            before["catalogVersion"] != after["catalogVersion"],
            "Body correction changes catalog version",
        )
        get(
            path + "/chapters?catalogVersion=" + before["catalogVersion"],
            status=409,
            model="ErrorResponse",
        )
        media_before, _ = get(
            "/api/v1/books/image-book/updates", profile="updates", model="UpdateState"
        )
        with source.lock:
            source.assets["page-1.png"], source.assets["page-2.png"] = (
                source.assets["page-2.png"],
                source.assets["page-1.png"],
            )
        media_after, _ = get(
            "/api/v1/books/image-book/updates", profile="updates", model="UpdateState"
        )
        check(
            media_before["catalogVersion"] != media_after["catalogVersion"],
            "Ordered media revisions invalidate catalog",
        )
        rankings, _ = get("/api/v1/rankings", model="RankingCollection")
        check(len(rankings["items"]) >= 2, "Multiple ranking definitions")
        first, _ = get("/api/v1/rankings/weekly?pageSize=2", model="RankingPage")
        second, _ = get(
            "/api/v1/rankings/weekly?page=2&pageSize=2", model="RankingPage"
        )
        check(
            first["snapshotId"] == second["snapshotId"], "Consistent ranking snapshot"
        )
        check(
            [item["rank"] for item in first["items"] + second["items"]] == [1, 2, 3, 4],
            "Absolute ranks across pages",
        )
        get("/api/v1/rankings/unknown", status=404, model="ErrorResponse")
        get(
            "/api/v1/books/text-book/chapters?pageSize=101",
            status=400,
            model="ErrorResponse",
        )
        report = probe(
            base + "/.well-known/open-reading-source.json",
            transport=Transport(allow_loopback=True),
        )
        check(
            not report["issues"]
            and all(not item["issues"] for item in report["checks"]),
            "Read-only probe passes complete reference",
        )
        check(
            "Corrected original text" not in json.dumps(report),
            "Probe output does not retain chapter contents",
        )
        for url in (
            "http://127.0.0.1/a",
            "http://10.0.0.1/a",
            "http://user:secret@example.org/a",
        ):
            try:
                Transport().get(url)
            except (ProbeError, RegistryError):
                check(True, "Probe prevents private/credential target")
            else:
                raise AssertionError("Accepted forbidden probe target")
    finally:
        source.close()
    print(f"Complete reading profile validation passed: {checks} checks")


if __name__ == "__main__":
    main()
