"""File-backed source snapshots. Replace this adapter without changing ORSP HTTP."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock

MAX_LIBRARY_BYTES = 8 * 1024 * 1024
TOKEN = re.compile(r"^[A-Za-z0-9._~-]{1,200}$")
SOURCE_ID = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")


def encode(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def text(value, maximum):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise ValueError("Invalid string field")
    return value.strip()


def token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError("Invalid content identifier")
    return value


def timestamp(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("Invalid timestamp")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires timezone")
    return parsed.astimezone(UTC).isoformat()


@dataclass(frozen=True)
class Book:
    detail: dict
    catalog: tuple
    content: dict
    updates: dict


@dataclass(frozen=True)
class Snapshot:
    source_id: str
    name: str
    books: dict[str, Book]


def parse_library(value):
    source_id = text(value["id"], 200)
    if len(source_id) < 3 or not SOURCE_ID.fullmatch(source_id):
        raise ValueError("Invalid source identifier")
    name = text(value["name"], 120)
    books = {}
    for item in value["books"]:
        book_id = token(item["id"])
        if book_id in books:
            raise ValueError("Duplicate book identifier")
        detail = {
            "id": book_id,
            "title": text(item["title"], 500),
            "type": 8,
            "mediaKind": "text",
        }
        for key in ("author", "description"):
            if key in item:
                detail[key] = text(
                    item[key], 500 if key == "author" else MAX_LIBRARY_BYTES
                )
        if "updatedAt" in item:
            detail["updatedAt"] = timestamp(item["updatedAt"])
        contents, catalog = {}, []
        for index, chapter in enumerate(item["chapters"]):
            chapter_id = token(chapter["id"])
            if chapter_id in contents:
                raise ValueError("Duplicate chapter identifier")
            title = text(chapter["title"], 500)
            body = chapter["content"]
            if not isinstance(body, str):
                raise TypeError("Chapter content must be text")
            order = chapter.get("order", index)
            if not isinstance(order, int) or isinstance(order, bool) or order < 0:
                raise ValueError("Invalid chapter order")
            version = hashlib.sha256(body.encode("utf-8")).hexdigest()
            summary = {
                "id": chapter_id,
                "title": title,
                "order": order,
                "contentVersion": version,
            }
            if "updatedAt" in chapter:
                summary["updatedAt"] = timestamp(chapter["updatedAt"])
            catalog.append(summary)
            contents[chapter_id] = {
                "bookId": book_id,
                "chapterId": chapter_id,
                "title": title,
                "contentType": "text/plain",
                "content": body,
                "contentVersion": version,
            }
        catalog.sort(key=lambda chapter: (chapter["order"], chapter["id"]))
        version = hashlib.sha256(encode(catalog)).hexdigest()
        detail.update(chapterCount=len(catalog), catalogVersion=version)
        updates = {
            "bookId": book_id,
            "chapterCount": len(catalog),
            "catalogVersion": version,
        }
        if catalog:
            detail["latestChapter"] = catalog[-1]["title"]
            updates["latestChapter"] = catalog[-1]
        if "updatedAt" in detail:
            updates["updatedAt"] = detail["updatedAt"]
        books[book_id] = Book(detail, tuple(catalog), contents, updates)
    return Snapshot(source_id, name, books)


class FileLibrary:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = RLock()
        self.signature = None
        self.snapshot = None
        self.get()

    def get(self):
        with self.lock:
            stat = self.path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if signature != self.signature:
                with self.path.open("rb") as stream:
                    data = stream.read(MAX_LIBRARY_BYTES + 1)
                if len(data) > MAX_LIBRARY_BYTES:
                    raise ValueError("Library exceeds starter size limit")
                candidate = parse_library(json.loads(data.decode("utf-8")))
                if self.snapshot and candidate.source_id != self.snapshot.source_id:
                    raise ValueError(
                        "Published source identity cannot change during reload"
                    )
                self.snapshot, self.signature = candidate, signature
            return self.snapshot
