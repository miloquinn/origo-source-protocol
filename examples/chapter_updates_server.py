"""Original sample source for OEP-0005. Operator mutations are in-process only."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import RLock, Thread
from urllib.parse import parse_qs, urlsplit

CAPABILITY = "top.xxread:chapter-updates"
BOOK_ID = "sample-book"
TOKEN = re.compile(r"^[A-Za-z0-9._~-]{1,200}$")


class ChapterUpdateSource:
    def __init__(self):
        self.lock = RLock()
        self.chapters = {}
        self.used_ids = set()
        self.revision = 0
        self.updated_at = datetime.now(UTC).isoformat()
        self.server = None

    def publish(self, identifier, title, content, order, *, updated_at=None):
        if not TOKEN.fullmatch(identifier) or order < 0:
            raise ValueError("Invalid chapter")
        with self.lock:
            if identifier in self.used_ids:
                raise ValueError("Chapter identity cannot be reused")
            self.used_ids.add(identifier)
            self.chapters[identifier] = {
                "id": identifier,
                "title": title,
                "content": content,
                "order": order,
                "updatedAt": updated_at or datetime.now(UTC).isoformat(),
            }
            self._changed(updated_at)

    def revise(
        self, identifier, *, title=None, content=None, order=None, updated_at=None
    ):
        with self.lock:
            chapter = self.chapters[identifier]
            for key, value in (
                ("title", title),
                ("content", content),
                ("order", order),
            ):
                if value is not None:
                    if key == "order" and value < 0:
                        raise ValueError("Invalid order")
                    chapter[key] = value
            chapter["updatedAt"] = updated_at or datetime.now(UTC).isoformat()
            self._changed(updated_at)

    def withdraw(self, identifier):
        with self.lock:
            del self.chapters[identifier]
            self._changed(None)

    def _changed(self, updated_at):
        self.revision += 1
        self.updated_at = updated_at or datetime.now(UTC).isoformat()

    def snapshot(self):
        with self.lock:
            chapters = deepcopy(
                sorted(self.chapters.values(), key=lambda x: (x["order"], x["id"]))
            )
            for chapter in chapters:
                chapter["contentVersion"] = hashlib.sha256(
                    chapter["content"].encode()
                ).hexdigest()
            metadata = [
                {key: value for key, value in chapter.items() if key != "content"}
                for chapter in chapters
            ]
            state = {
                "bookId": BOOK_ID,
                "catalogVersion": f"catalog-{self.revision}",
                "chapterCount": len(chapters),
                "updatedAt": self.updated_at,
            }
            if metadata:
                state["latestChapter"] = metadata[-1]
            return state, metadata, chapters

    def start(self):
        source = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def reply(self, status, value, *, cache="no-cache", allow=None):
                body = json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
                etag = '"' + hashlib.sha256(body).hexdigest() + '"'
                tags = re.findall(
                    r'(?:W/)?"[^"]*"|\*', self.headers.get("If-None-Match", "")
                )
                unchanged = status == 200 and (
                    "*" in tags or etag in [tag.removeprefix("W/") for tag in tags]
                )
                self.send_response(304 if unchanged else status)
                self.send_header("X-Origo-Source-Protocol", "1.5")
                self.send_header("X-Open-Reading-Protocol", "1.5")
                self.send_header(
                    "Cache-Control", cache if status == 200 else "no-store"
                )
                self.send_header("ETag", etag)
                if allow:
                    self.send_header("Allow", allow)
                if not unchanged:
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if not unchanged:
                    self.wfile.write(body)

            def error(self, status, code):
                self.reply(
                    status,
                    {"error": {"code": code, "message": code}},
                    allow="GET" if status == 405 else None,
                )

            def do_POST(self):
                self.error(405, "METHOD_NOT_ALLOWED")

            def do_GET(self):
                parsed = urlsplit(self.path)
                path, query = (
                    parsed.path,
                    parse_qs(parsed.query, keep_blank_values=True),
                )
                state, metadata, chapters = source.snapshot()
                book = {
                    "id": BOOK_ID,
                    "title": "Original serial sample",
                    "updatedAt": state["updatedAt"],
                    "catalogVersion": state["catalogVersion"],
                    "chapterCount": state["chapterCount"],
                }
                if metadata:
                    book["latestChapter"] = metadata[-1]["title"]
                if path in (
                    "/.well-known/origo-source.json",
                    "/.well-known/open-reading-source.json",
                ):
                    self.reply(
                        200,
                        {
                            "protocol": "open-reading-source"
                            if path.endswith("/open-reading-source.json")
                            else "origo-source",
                            "protocolVersion": "1.5",
                            "id": "org.example.chapter-updates",
                            "name": "Chapter update reference",
                            "apiBaseUrl": source.base_url + "/api/",
                            "capabilities": [
                                "search",
                                "detail",
                                "catalog",
                                "content",
                                CAPABILITY,
                            ],
                        },
                    )
                    return
                if path == "/api/v1/search":
                    q = query.get("q", [""])[0].strip()
                    try:
                        page, size = (
                            int(query.get("page", ["1"])[0]),
                            int(query.get("pageSize", ["20"])[0]),
                        )
                        if not 1 <= len(q) <= 200 or page < 1 or not 1 <= size <= 100:
                            raise ValueError
                    except ValueError:
                        self.error(400, "INVALID_PARAMETER")
                        return
                    self.reply(
                        200,
                        {
                            "items": [book]
                            if page == 1 and q.lower() in book["title"].lower()
                            else [],
                            "page": page,
                            "pageSize": size,
                            "hasMore": False,
                        },
                    )
                    return
                segments = path.strip("/").split("/")
                if len(segments) < 4 or segments[:3] != ["api", "v1", "books"]:
                    self.error(404, "ROUTE_NOT_FOUND")
                    return
                if segments[3] != BOOK_ID:
                    self.error(404, "BOOK_NOT_FOUND")
                    return
                if len(segments) == 4:
                    self.reply(200, book)
                    return
                if segments[4] == "updates" and len(segments) == 5:
                    self.reply(200, state)
                    return
                if segments[4] != "chapters" or len(segments) not in (5, 6):
                    self.error(404, "ROUTE_NOT_FOUND")
                    return
                expected = query.get("catalogVersion", [None])[0]
                if expected is not None:
                    if not TOKEN.fullmatch(expected):
                        self.error(400, "INVALID_PARAMETER")
                        return
                    if expected != state["catalogVersion"]:
                        self.error(409, "X_CATALOG_VERSION_CONFLICT")
                        return
                if len(segments) == 6:
                    chapter = next(
                        (x for x in chapters if x["id"] == segments[5]), None
                    )
                    if chapter is None:
                        self.error(404, "CHAPTER_NOT_FOUND")
                        return
                    self.reply(
                        200,
                        {
                            **chapter,
                            "bookId": BOOK_ID,
                            "chapterId": chapter["id"],
                            "contentType": "text/plain",
                        },
                    )
                    return
                try:
                    page, size = (
                        int(query.get("page", ["1"])[0]),
                        int(query.get("pageSize", ["100"])[0]),
                    )
                    if page < 1 or not 1 <= size <= 100:
                        raise ValueError
                except ValueError:
                    self.error(400, "INVALID_PARAMETER")
                    return
                start = (page - 1) * size
                self.reply(
                    200,
                    {
                        "items": metadata[start : start + size],
                        "page": page,
                        "pageSize": size,
                        "total": len(metadata),
                        "hasMore": start + size < len(metadata),
                        "catalogVersion": state["catalogVersion"],
                    },
                )

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
    source = ChapterUpdateSource()
    source.publish("chapter-1", "First chapter", "Original sample text.", 0)
    print(source.start(), flush=True)
    try:
        source.thread.join()
    except KeyboardInterrupt:
        source.close()
