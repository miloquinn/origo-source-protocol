"""Unit tests for registry validation and network-safety helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import registry_tool


class RegistryToolTests(unittest.TestCase):
    def test_example_and_empty_registry_are_valid(self) -> None:
        entries = registry_tool.validate_entries()
        self.assertEqual(entries, [])
        errors = registry_tool.format_validation_errors(
            registry_tool.registry_validator(),
            registry_tool.generated_document(entries),
        )
        self.assertEqual(errors, [])

    def test_global_ip_is_allowed(self) -> None:
        self.assertEqual(str(registry_tool.ensure_global_ip("8.8.8.8")), "8.8.8.8")

    def test_loopback_and_private_ips_are_rejected(self) -> None:
        rejected = [
            "127.0.0.1",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.1.1",
            "169.254.169.254",
            "::1",
            "fc00::1",
        ]
        for value in rejected:
            with self.subTest(value=value):
                with self.assertRaises(registry_tool.RegistryError):
                    registry_tool.ensure_global_ip(value)

    def test_id_validation(self) -> None:
        self.assertEqual(registry_tool.require_id("book-1", "ID"), "book-1")
        for value in ["", "book/1", "book%201", "章节一"]:
            with self.subTest(value=value):
                with self.assertRaises(registry_tool.RegistryError):
                    registry_tool.require_id(value, "ID")

    def test_non_https_and_user_info_are_rejected_without_dns(self) -> None:
        with self.assertRaises(registry_tool.RegistryError):
            registry_tool.validate_public_https_url("http://example.com/source")
        with self.assertRaises(registry_tool.RegistryError):
            registry_tool.validate_public_https_url(
                "https://user:password@example.com/source"
            )

    def test_direct_private_network_url_is_rejected(self) -> None:
        with self.assertRaises(registry_tool.RegistryError):
            registry_tool.validate_public_https_url("https://127.0.0.1/source")

    def test_unexpected_source_directory_files_are_rejected(self) -> None:
        original = registry_tool.SOURCES_DIR
        with TemporaryDirectory() as directory:
            registry_tool.SOURCES_DIR = Path(directory)
            (registry_tool.SOURCES_DIR / "notes.txt").write_text(
                "not a manifest",
                encoding="utf-8",
            )
            try:
                with self.assertRaises(registry_tool.RegistryError):
                    registry_tool.validate_sources_directory()
            finally:
                registry_tool.SOURCES_DIR = original


if __name__ == "__main__":
    unittest.main()
