"""Zero-dependency Origo Source starter: text, browse and chapter updates."""

from __future__ import annotations

import argparse
import hashlib
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from library import TOKEN, FileLibrary, encode

PROTOCOL_VERSION = "1.6"
CATALOG_PAGE_SIZE = 200


def public_origin(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or any(char.isspace() for char in value)
    ):
        raise ValueError(
            "public-origin must be an HTTP(S) origin without credentials or a path"
        )
    if parsed.port is not None and parsed.port < 1:
        raise ValueError("Invalid public port")
    return value.rstrip("/")


def create_server(library_path, *, host="127.0.0.1", port=8787, origin=None):
    library = FileLibrary(library_path)
    advertised_origin = public_origin(origin) if origin else None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, value, status=200, headers=None):
            body = encode(value)
            etag = '"' + hashlib.sha256(body).hexdigest() + '"'
            tags = re.findall(
                r'(?:W/)?"[^"]*"|\*', self.headers.get("If-None-Match", "")
            )
            unchanged = status == 200 and (
                "*" in tags or etag in [tag.removeprefix("W/") for tag in tags]
            )
            self.send_response(304 if unchanged else status)
            self.send_header("ETag", etag)
            self.send_header("X-Open-Reading-Protocol", PROTOCOL_VERSION)
            self.send_header(
                "Cache-Control", "no-cache" if status == 200 else "no-store"
            )
            for key, header_value in (headers or {}).items():
                self.send_header(key, header_value)
            if not unchanged:
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not unchanged and self.command != "HEAD":
                self.wfile.write(body)

        def error(self, status, code):
            self.reply(
                {"error": {"code": code, "message": code}},
                status,
                {"Allow": "GET"} if status == 405 else None,
            )

        def do_POST(self):
            self.error(405, "METHOD_NOT_ALLOWED")

        do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = do_POST

        def do_GET(self):
            try:
                self.read(library.get())
            except (OSError, ValueError, KeyError, TypeError):
                self.error(503, "UNAVAILABLE")

        def read(self, snapshot):
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query, keep_blank_values=True)
            path = parsed.path
            if path == "/.well-known/open-reading-source.json":
                base = (
                    advertised_origin or f"http://127.0.0.1:{self.server.server_port}"
                )
                self.reply(
                    {
                        "protocol": "open-reading-source",
                        "protocolVersion": PROTOCOL_VERSION,
                        "id": snapshot.source_id,
                        "name": snapshot.name,
                        "apiBaseUrl": base + "/api/",
                        "capabilities": [
                            "search",
                            "detail",
                            "catalog",
                            "content",
                            "browse",
                            "top.xxread:chapter-updates",
                        ],
                        "contentTypes": ["text/plain"],
                        "maxCatalogPageSize": CATALOG_PAGE_SIZE,
                    }
                )
                return
            try:
                page = int(query.get("page", ["1"])[0])
                size = int(
                    query.get(
                        "pageSize", ["100" if path.endswith("/chapters") else "20"]
                    )[0]
                )
                maximum = CATALOG_PAGE_SIZE if path.endswith("/chapters") else 100
                if page < 1 or not 1 <= size <= maximum:
                    raise ValueError
            except ValueError:
                self.error(400, "INVALID_PARAMETER")
                return
            start = (page - 1) * size
            if path in ("/api/v1/search", "/api/v1/browse"):
                term = query.get("q", [""])[0].strip()
                if path.endswith("search") and not 1 <= len(term) <= 200:
                    self.error(400, "INVALID_PARAMETER")
                    return
                if "category" in query or query.get("sort", ["latest"])[0] not in (
                    "latest",
                    "popular",
                ):
                    self.error(400, "INVALID_PARAMETER")
                    return
                books = sorted(
                    snapshot.books.values(),
                    key=lambda book: (
                        book.detail.get("updatedAt", ""),
                        book.detail["id"],
                    ),
                    reverse=True,
                )
                items = [
                    book.detail
                    for book in books
                    if not term
                    or term.casefold()
                    in (
                        book.detail["title"] + " " + book.detail.get("author", "")
                    ).casefold()
                ]
                self.reply(
                    {
                        "items": items[start : start + size],
                        "page": page,
                        "pageSize": size,
                        "total": len(items),
                        "hasMore": start + size < len(items),
                    }
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
            if book_id not in snapshot.books:
                self.error(404, "BOOK_NOT_FOUND")
                return
            book = snapshot.books[book_id]
            if len(parts) == 4:
                self.reply(book.detail)
                return
            if len(parts) == 5 and parts[4] == "updates":
                self.reply(book.updates)
                return
            if parts[4] != "chapters" or len(parts) not in (5, 6):
                self.error(404, "ROUTE_NOT_FOUND")
                return
            version = query.get("catalogVersion", [None])[0]
            if version is not None and not TOKEN.fullmatch(version):
                self.error(400, "INVALID_PARAMETER")
                return
            if version is not None and version != book.updates["catalogVersion"]:
                self.error(409, "X_CATALOG_VERSION_CONFLICT")
                return
            if len(parts) == 5:
                self.reply(
                    {
                        "items": list(book.catalog[start : start + size]),
                        "page": page,
                        "pageSize": size,
                        "total": len(book.catalog),
                        "hasMore": start + size < len(book.catalog),
                        "catalogVersion": book.updates["catalogVersion"],
                    }
                )
                return
            chapter_id = parts[5]
            if not TOKEN.fullmatch(chapter_id):
                self.error(400, "INVALID_PARAMETER")
                return
            if chapter_id not in book.content:
                self.error(404, "CHAPTER_NOT_FOUND")
                return
            self.reply(book.content[chapter_id])

    return ThreadingHTTPServer((host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--library", type=Path, default=Path(__file__).with_name("library.json")
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--public-origin", type=public_origin)
    args = parser.parse_args()
    server = create_server(
        args.library, host=args.host, port=args.port, origin=args.public_origin
    )
    print(f"Origo Source listening on {args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
