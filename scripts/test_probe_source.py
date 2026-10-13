"""Regression tests for imperfect sources, bounded sampling and private data."""

import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import urlsplit

import registry_tool
from probe_source import probe


class FixtureTransport:
    def __init__(self):
        self.requests = []
        self.responses = {
            "/.well-known/open-reading-source.json": {
                "protocol": "open-reading-source",
                "protocolVersion": "1.1",
                "id": "org.example.probe",
                "name": "Original sample",
                "apiBaseUrl": "https://example.org/api/",
                "capabilities": ["search", "detail", "catalog", "content"],
            },
            "/api/v1/search": {
                "items": [{"id": "book-1", "title": "Original"}],
                "page": 1,
                "pageSize": 1,
                "hasMore": False,
            },
            "/api/v1/books/book-1": {"id": "book-1", "title": "Original"},
            "/api/v1/books/book-1/chapters": {
                "items": [{"id": "chapter-1", "title": "First", "order": 0}],
                "page": 1,
                "pageSize": 1,
                "hasMore": False,
            },
            "/api/v1/books/book-1/chapters/chapter-1": {
                "bookId": "book-1",
                "chapterId": "chapter-1",
                "title": "First",
                "contentType": "text/plain",
                "content": "Private sample body: never include this in diagnostics.",
            },
        }

    def get(self, url, **_kwargs):
        path = urlsplit(url).path
        self.requests.append(path)
        return (
            200,
            {"content-type": "application/json; charset=utf-8"},
            json.dumps(self.responses[path]).encode(),
        )


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.transport = FixtureTransport()

    def run_probe(self):
        return probe(
            "https://example.org/.well-known/open-reading-source.json",
            transport=self.transport,
        )

    def test_legacy_without_optional_capabilities_stays_readable(self):
        report = self.run_probe()
        self.assertFalse(report["issues"])
        self.assertTrue(all(not check["issues"] for check in report["checks"]))
        self.assertEqual(len(self.transport.requests), 5)
        self.assertNotIn("Private sample body", json.dumps(report))

    def test_missing_title_is_strict_failure_with_reader_fallback_explanation(self):
        self.transport.responses["/api/v1/books/book-1/chapters/chapter-1"].pop("title")
        report = self.run_probe()
        self.assertTrue(report["checks"][-1]["issues"])
        self.assertIn("Required title", " ".join(report["checks"][-1]["issues"]))
        self.assertNotIn("Private sample body", json.dumps(report))

    def test_mismatched_identity_is_not_reported_as_compatible(self):
        self.transport.responses["/api/v1/books/book-1/chapters/chapter-1"][
            "bookId"
        ] = "other-book"
        report = self.run_probe()
        self.assertIn(
            "Content IDs do not match request", report["checks"][-1]["issues"]
        )

    def test_invalid_discovery_does_not_trigger_api_fetch(self):
        self.transport.responses["/.well-known/open-reading-source.json"][
            "apiBaseUrl"
        ] = "https://user:secret@example.org/api/"
        report = self.run_probe()
        self.assertTrue(report["issues"])
        self.assertEqual(len(self.transport.requests), 1)
        self.assertNotIn("secret", json.dumps(report))

    def test_empty_source_reports_incomplete_sampling(self):
        self.transport.responses["/api/v1/search"]["items"] = []
        report = self.run_probe()
        self.assertIn("No book sampled", " ".join(report["issues"]))
        self.assertEqual(len(self.transport.requests), 2)

    def test_invalid_search_shape_does_not_crash_or_fetch_arbitrary_ids(self):
        self.transport.responses["/api/v1/search"]["items"] = "malformed"
        report = self.run_probe()
        self.assertTrue(report["checks"][-1]["issues"])
        self.assertEqual(len(self.transport.requests), 2)

    def test_non_json_media_selector_is_diagnosed_without_crashing(self):
        self.transport.responses["/api/v1/books/book-1/chapters/chapter-1"][
            "contentType"
        ] = {"unexpected": "object"}
        report = self.run_probe()
        self.assertTrue(report["checks"][-1]["issues"])

    def test_unknown_capability_does_not_trigger_unapproved_endpoint(self):
        manifest = self.transport.responses["/.well-known/open-reading-source.json"]
        manifest["capabilities"] = copy.deepcopy(manifest["capabilities"]) + [
            "org.example:future"
        ]
        report = self.run_probe()
        self.assertFalse(report["issues"])
        self.assertEqual(len(self.transport.requests), 5)

    def test_registry_diagnostic_accepts_declared_media_and_rejects_missing_title(self):
        manifest = self.transport.responses["/.well-known/open-reading-source.json"]
        manifest["capabilities"].append("top.xxread:remote-audio")
        manifest["contentTypes"] = ["audio/uri"]
        content = self.transport.responses["/api/v1/books/book-1/chapters/chapter-1"]
        content.update(
            contentType="audio/uri",
            content="",
            audio={"url": "https://example.org/sample.wav", "mimeType": "audio/wav"},
        )
        entry = registry_tool.load_json(registry_tool.EXAMPLE_ENTRY_PATH)
        entry.update(
            id=manifest["id"],
            discoveryUrl="https://example.org/.well-known/open-reading-source.json",
        )

        def request(url, _label):
            body = self.transport.responses[urlsplit(url).path]
            return body, registry_tool.HttpResult(
                url, 200, {}, json.dumps(body).encode(), 1
            )

        with TemporaryDirectory() as directory:
            file = Path(directory) / "source.json"
            file.write_text(json.dumps(entry), encoding="utf-8")
            with (
                patch.object(registry_tool, "require_json", side_effect=request),
                patch.object(
                    registry_tool, "resolve_public_addresses", return_value=["8.8.8.8"]
                ),
            ):
                report = registry_tool.check_source(file)
                self.assertEqual(report["status"], "verified")
                content.pop("title")
                with self.assertRaises(registry_tool.RegistryError):
                    registry_tool.check_source(file)


if __name__ == "__main__":
    unittest.main()
