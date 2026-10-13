"""ORSP 1.6 reference: original text, image, audio and EPUB fixtures only."""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
import struct
import wave
import zlib
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import RLock, Thread
from urllib.parse import parse_qs, urlsplit
from zipfile import ZIP_STORED, ZipFile, ZipInfo

IMAGE_CAPABILITY = "top.xxread:image-sequence"
AUDIO_CAPABILITY = "top.xxread:remote-audio"
UPDATE_CAPABILITY = "top.xxread:chapter-updates"
PUBLICATION_CAPABILITY = "top.xxread:publications"
TOKEN = re.compile(r"^[A-Za-z0-9._~-]{1,200}$")


def png(red: int) -> bytes:
    def chunk(name, data):
        return (
            struct.pack(">I", len(data))
            + name
            + data
            + struct.pack(">I", zlib.crc32(name + data))
        )

    pixels = b"".join(b"\0" + bytes([red, 130, 90]) * 16 for _ in range(16))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def wav() -> bytes:
    stream = io.BytesIO()
    with wave.open(stream, "wb") as output:
        output.setparams((1, 2, 8000, 0, "NONE", "not compressed"))
        output.writeframes(
            b"".join(
                struct.pack("<h", int(2000 * math.sin(i * 2 * math.pi * 440 / 8000)))
                for i in range(16000)
            )
        )
    return stream.getvalue()


def epub() -> bytes:
    stream = io.BytesIO()
    with ZipFile(stream, "w") as archive:

        def write(name, data):
            # Repeated starts produce the same immutable publication bytes.
            info = ZipInfo(name, date_time=(2026, 10, 13, 0, 0, 0))
            info.compress_type = ZIP_STORED
            archive.writestr(info, data)

        write("mimetype", "application/epub+zip")
        write(
            "META-INF/container.xml",
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        write(
            "OPS/package.opf",
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">urn:orsp:original-sample</dc:identifier><dc:title>Original reading sample</dc:title><dc:language>en</dc:language><meta property="dcterms:modified">2026-10-13T00:00:00Z</meta></metadata><manifest><item id="text" href="text.xhtml" media-type="application/xhtml+xml"/><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/></manifest><spine><itemref idref="text"/></spine></package>',
        )
        write(
            "OPS/text.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Original chapter</title></head><body><h1>Original chapter</h1><p>Give reading a little time.</p></body></html>',
        )
        write(
            "OPS/nav.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Contents</title></head><body><nav epub:type="toc"><ol><li><a href="text.xhtml">Original chapter</a></li></ol></nav></body></html>',
        )
    return stream.getvalue()


class ReadingProfileSource:
    def __init__(self):
        self.lock = RLock()
        self.server = None
        self.audio_reads = 0
        self.updated_at = datetime.now(UTC).isoformat()
        self.audio_expiry = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        self.assets = {
            "page-1.png": (png(90), "image/png"),
            "page-2.png": (png(190), "image/png"),
            "chapter.wav": (wav(), "audio/wav"),
            "original.epub": (epub(), "application/epub+zip"),
        }
        self.books = {
            "text-book": {
                "title": "Original text",
                "kind": "text",
                "type": 8,
                "chapters": [
                    {
                        "id": "text-1",
                        "title": "First text",
                        "order": 0,
                        "text": "Give reading a little time.",
                    }
                ],
            },
            "image-book": {
                "title": "Original picture pages",
                "kind": "image-sequence",
                "type": 64,
                "chapters": [{"id": "image-1", "title": "First pictures", "order": 0}],
            },
            "audio-book": {
                "title": "Original recording",
                "kind": "remote-audio",
                "type": 32,
                "chapters": [{"id": "audio-1", "title": "First recording", "order": 0}],
            },
            "epub-book": {
                "title": "Original EPUB",
                "kind": "text",
                "type": 8,
                "chapters": [
                    {
                        "id": "epub-1",
                        "title": "Original chapter",
                        "order": 0,
                        "text": "Give reading a little time.",
                    }
                ],
            },
            "markdown-book": {
                "title": "Original illustrated article",
                "kind": "text",
                "type": 8,
                "chapters": [
                    {
                        "id": "markdown-1",
                        "title": "Illustrated note",
                        "order": 0,
                        "text": "# A little time\n\n![Original picture](page-1.png)\n\nGive reading a little time.",
                    }
                ],
            },
        }

    def chapter(self, book_id, chapter, *, refresh=False):
        book = self.books[book_id]
        value = {
            "bookId": book_id,
            "chapterId": chapter["id"],
            "title": chapter["title"],
            "contentType": "text/plain",
            "content": chapter.get("text", ""),
        }
        kind = book["kind"]
        if kind == "image-sequence":
            value.update(
                contentType="image/sequence",
                content="",
                images=[
                    {
                        "url": self.base_url + "/assets/" + name,
                        "mimeType": "image/png",
                        "width": 16,
                        "height": 16,
                        "alt": "Original sample page",
                    }
                    for name in ("page-1.png", "page-2.png")
                ],
            )
            digest = json.dumps(
                {
                    "contentType": value["contentType"],
                    "assets": [
                        {
                            **{k: v for k, v in image.items() if k != "url"},
                            "sha256": hashlib.sha256(self.assets[name][0]).hexdigest(),
                        }
                        for image, name in zip(
                            value["images"], ("page-1.png", "page-2.png"), strict=True
                        )
                    ],
                },
                sort_keys=True,
            ).encode()
        elif kind == "remote-audio":
            if refresh:
                self.audio_reads += 1
            expired = self.audio_reads <= 1
            value.update(
                contentType="audio/uri",
                content="",
                audio={
                    "url": self.base_url
                    + ("/assets/expired.wav" if expired else "/assets/chapter.wav"),
                    "mimeType": "audio/wav",
                    "durationSeconds": 2,
                    "transport": "file",
                    "expiresAt": "2000-01-01T00:00:00Z"
                    if expired
                    else self.audio_expiry,
                },
            )
            digest = json.dumps(
                {
                    "contentType": value["contentType"],
                    "asset": {
                        **{
                            k: v
                            for k, v in value["audio"].items()
                            if k not in ("url", "expiresAt")
                        },
                        "sha256": hashlib.sha256(
                            self.assets["chapter.wav"][0]
                        ).hexdigest(),
                    },
                },
                sort_keys=True,
            ).encode()
        else:
            if book_id == "markdown-book":
                value.update(
                    contentType="text/markdown", baseUrl=self.base_url + "/assets/"
                )
            digest = value["content"].encode()
        value["contentVersion"] = hashlib.sha256(digest).hexdigest()
        return value

    def snapshot(self, book_id):
        book = self.books[book_id]
        chapters = [
            {
                "id": c["id"],
                "title": c["title"],
                "order": c["order"],
                "updatedAt": self.updated_at,
                "contentVersion": self.chapter(book_id, c)["contentVersion"],
            }
            for c in sorted(book["chapters"], key=lambda x: (x["order"], x["id"]))
        ]
        publication_hash = (
            hashlib.sha256(self.assets["original.epub"][0]).hexdigest()
            if book_id == "epub-book"
            else ""
        )
        version = hashlib.sha256(
            json.dumps([chapters, publication_hash], sort_keys=True).encode()
        ).hexdigest()
        state = {
            "bookId": book_id,
            "catalogVersion": version,
            "chapterCount": len(chapters),
            "updatedAt": self.updated_at,
        }
        if chapters:
            state["latestChapter"] = chapters[-1]
        return state, chapters

    def metadata(self, book_id):
        book = self.books[book_id]
        state, chapters = self.snapshot(book_id)
        return {
            "id": book_id,
            "title": book["title"],
            "author": "ORSP reference",
            "categories": [book["kind"]],
            "mediaKind": book["kind"],
            "type": book["type"],
            "updatedAt": self.updated_at,
            "catalogVersion": state["catalogVersion"],
            "chapterCount": len(chapters),
            "latestChapter": chapters[-1]["title"] if chapters else "",
            "license": "CC0-1.0",
        }

    def publications(self, book_id):
        if book_id != "epub-book":
            return []
        data = self.assets["original.epub"][0]
        return [
            {
                "id": "original-epub-" + hashlib.sha256(data).hexdigest()[:16],
                "href": self.base_url + "/assets/original.epub",
                "mediaType": "application/epub+zip",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ]

    def revise_text(self, text):
        with self.lock:
            self.books["text-book"]["chapters"][0]["text"] = text

    def start(self):
        source = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def reply(
                self,
                status,
                data,
                mime="application/json",
                headers=None,
                representation_etag=None,
            ):
                binary = isinstance(data, bytes)
                body = (
                    data
                    if binary
                    else json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
                )
                etag = representation_etag or (
                    '"' + hashlib.sha256(body).hexdigest() + '"'
                )
                tags = re.findall(
                    r'(?:W/)?"[^"]*"|\*', self.headers.get("If-None-Match", "")
                )
                not_modified = status == 200 and (
                    "*" in tags or etag in [tag.removeprefix("W/") for tag in tags]
                )
                self.send_response(304 if not_modified else status)
                self.send_header("X-Open-Reading-Protocol", "1.6")
                self.send_header("ETag", etag)
                self.send_header(
                    "Cache-Control", "no-cache" if status < 400 else "no-store"
                )
                for name, value in (headers or {}).items():
                    self.send_header(name, value)
                if not not_modified:
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if not not_modified and self.command != "HEAD":
                    self.wfile.write(body)

            def error(self, status, code, headers=None):
                self.reply(
                    status,
                    {"error": {"code": code, "message": code}},
                    headers={"Allow": "GET"} if status == 405 else headers,
                )

            def do_POST(self):
                self.error(405, "METHOD_NOT_ALLOWED")

            do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = do_POST

            def do_GET(self):
                with source.lock:
                    self.handle_read()

            def handle_read(self):
                parsed = urlsplit(self.path)
                path, query = (
                    parsed.path,
                    parse_qs(parsed.query, keep_blank_values=True),
                )
                if path == "/.well-known/open-reading-source.json":
                    self.reply(
                        200,
                        {
                            "protocol": "open-reading-source",
                            "protocolVersion": "1.6",
                            "id": "org.example.reading-profiles",
                            "name": "Complete reading reference",
                            "apiBaseUrl": source.base_url + "/api/",
                            "languages": ["en"],
                            "capabilities": [
                                "search",
                                "detail",
                                "catalog",
                                "content",
                                "discover",
                                "categories",
                                "browse",
                                "rankings",
                                IMAGE_CAPABILITY,
                                AUDIO_CAPABILITY,
                                UPDATE_CAPABILITY,
                                PUBLICATION_CAPABILITY,
                            ],
                            "contentTypes": [
                                "text/plain",
                                "text/markdown",
                                "image/sequence",
                                "audio/uri",
                            ],
                        },
                    )
                    return
                if path.startswith("/assets/"):
                    name = path.removeprefix("/assets/")
                    if name == "expired.wav":
                        self.error(403, "X_MEDIA_EXPIRED")
                        return
                    if name not in source.assets:
                        self.error(404, "ROUTE_NOT_FOUND")
                        return
                    data, mime = source.assets[name]
                    asset_etag = '"' + hashlib.sha256(data).hexdigest() + '"'
                    range_header = self.headers.get("Range")
                    tags = re.findall(
                        r'(?:W/)?"[^"]*"|\*', self.headers.get("If-None-Match", "")
                    )
                    if "*" in tags or asset_etag in [
                        tag.removeprefix("W/") for tag in tags
                    ]:
                        self.reply(200, data, mime, {"Accept-Ranges": "bytes"})
                        return
                    if self.headers.get("If-Range") not in (None, asset_etag):
                        range_header = None
                    if range_header:
                        matched = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header)
                        if not matched:
                            self.error(
                                416,
                                "X_INVALID_RANGE",
                                {"Content-Range": f"bytes */{len(data)}"},
                            )
                            return
                        if not matched[1] and not matched[2]:
                            self.error(
                                416,
                                "X_INVALID_RANGE",
                                {"Content-Range": f"bytes */{len(data)}"},
                            )
                            return
                        start = (
                            int(matched[1])
                            if matched[1]
                            else max(0, len(data) - int(matched[2]))
                        )
                        end = (
                            int(matched[2])
                            if matched[1] and matched[2]
                            else len(data) - 1
                        )
                        if start >= len(data) or end < start:
                            self.error(
                                416,
                                "X_INVALID_RANGE",
                                {"Content-Range": f"bytes */{len(data)}"},
                            )
                            return
                        end = min(end, len(data) - 1)
                        self.reply(
                            206,
                            data[start : end + 1],
                            mime,
                            {
                                "Content-Range": f"bytes {start}-{end}/{len(data)}",
                                "Accept-Ranges": "bytes",
                            },
                            representation_etag=asset_etag,
                        )
                    else:
                        self.reply(200, data, mime, {"Accept-Ranges": "bytes"})
                    return
                try:
                    default_size = "100" if path.endswith("/chapters") else "20"
                    page, size = (
                        int(query.get("page", ["1"])[0]),
                        int(query.get("pageSize", [default_size])[0]),
                    )
                    if page < 1 or not 1 <= size <= 100:
                        raise ValueError
                except ValueError:
                    self.error(400, "INVALID_PARAMETER")
                    return
                start = (page - 1) * size
                if path == "/api/v1/categories":
                    self.reply(
                        200,
                        {
                            "items": [
                                {"id": kind, "name": kind}
                                for kind in ("text", "image-sequence", "remote-audio")
                            ]
                        },
                    )
                    return
                if path == "/api/v1/discover":
                    self.reply(
                        200,
                        {
                            "sections": [
                                {
                                    "id": "samples",
                                    "title": "Original samples",
                                    "items": [
                                        source.metadata(key) for key in source.books
                                    ],
                                }
                            ]
                        },
                    )
                    return
                if path in ("/api/v1/search", "/api/v1/browse"):
                    q = query.get("q", [""])[0].strip()
                    category = query.get("category", [None])[0]
                    if path.endswith("search") and not 1 <= len(q) <= 200:
                        self.error(400, "INVALID_PARAMETER")
                        return
                    if category not in (
                        None,
                        "text",
                        "image-sequence",
                        "remote-audio",
                    ) or query.get("sort", ["latest"])[0] not in ("latest", "popular"):
                        self.error(400, "INVALID_PARAMETER")
                        return
                    items = [
                        source.metadata(key)
                        for key, book in source.books.items()
                        if (not q or q.lower() in book["title"].lower())
                        and (category is None or category == book["kind"])
                    ]
                    self.reply(
                        200,
                        {
                            "items": items[start : start + size],
                            "page": page,
                            "pageSize": size,
                            "hasMore": start + size < len(items),
                        },
                    )
                    return
                definitions = {
                    "weekly": {
                        "id": "weekly",
                        "title": "Weekly sample",
                        "period": "weekly",
                    },
                    "latest": {
                        "id": "latest",
                        "title": "Latest sample",
                        "period": "realtime",
                    },
                }
                if path == "/api/v1/rankings":
                    self.reply(200, {"items": list(definitions.values())})
                    return
                if path.startswith("/api/v1/rankings/"):
                    ranking = path.removeprefix("/api/v1/rankings/")
                    if not TOKEN.fullmatch(ranking):
                        self.error(400, "INVALID_PARAMETER")
                        return
                    if ranking not in definitions:
                        self.error(404, "RANKING_NOT_FOUND")
                        return
                    keys = list(source.books)
                    self.reply(
                        200,
                        {
                            "ranking": definitions[ranking],
                            "snapshotId": "samples-1",
                            "items": [
                                {"rank": i + 1, "book": source.metadata(key)}
                                for i, key in enumerate(keys)
                                if start <= i < start + size
                            ],
                            "page": page,
                            "pageSize": size,
                            "total": len(keys),
                            "hasMore": start + size < len(keys),
                        },
                    )
                    return
                parts = path.strip("/").split("/")
                if len(parts) < 4 or parts[:3] != ["api", "v1", "books"]:
                    self.error(404, "ROUTE_NOT_FOUND")
                    return
                book_id = parts[3]
                if not TOKEN.fullmatch(book_id):
                    self.error(400, "INVALID_PARAMETER")
                    return
                if book_id not in source.books:
                    self.error(404, "BOOK_NOT_FOUND")
                    return
                state, chapters = source.snapshot(book_id)
                if len(parts) == 4:
                    self.reply(
                        200,
                        {
                            **source.metadata(book_id),
                            "publications": source.publications(book_id),
                        },
                    )
                    return
                if len(parts) == 5 and parts[4] == "updates":
                    self.reply(200, state)
                    return
                if len(parts) == 5 and parts[4] == "publications":
                    self.reply(200, {"items": source.publications(book_id)})
                    return
                if parts[4] == "chapters" and len(parts) in (5, 6):
                    expected = query.get("catalogVersion", [None])[0]
                    if expected is not None and not TOKEN.fullmatch(expected):
                        self.error(400, "INVALID_PARAMETER")
                        return
                    if expected is not None and expected != state["catalogVersion"]:
                        self.error(409, "X_CATALOG_VERSION_CONFLICT")
                        return
                    if len(parts) == 5:
                        self.reply(
                            200,
                            {
                                "items": chapters[start : start + size],
                                "page": page,
                                "pageSize": size,
                                "total": len(chapters),
                                "hasMore": start + size < len(chapters),
                                "catalogVersion": state["catalogVersion"],
                            },
                        )
                        return
                    if not TOKEN.fullmatch(parts[5]):
                        self.error(400, "INVALID_PARAMETER")
                        return
                    chapter = next(
                        (
                            c
                            for c in source.books[book_id]["chapters"]
                            if c["id"] == parts[5]
                        ),
                        None,
                    )
                    if chapter is None:
                        self.error(404, "CHAPTER_NOT_FOUND")
                        return
                    self.reply(200, source.chapter(book_id, chapter, refresh=True))
                    return
                self.error(404, "ROUTE_NOT_FOUND")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.base_url

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)


if __name__ == "__main__":
    source = ReadingProfileSource()
    print(source.start(), flush=True)
    try:
        source.thread.join()
    except KeyboardInterrupt:
        source.close()
