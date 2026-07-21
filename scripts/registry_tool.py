"""Build and validate the ORSP community source registry."""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import socket
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urljoin, urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "registry" / "sources"
GENERATED_REGISTRY = ROOT / "registry" / "generated" / "registry.json"
SOURCE_SCHEMA_PATH = ROOT / "registry" / "schemas" / "source-entry.schema.json"
REGISTRY_SCHEMA_PATH = ROOT / "registry" / "schemas" / "registry.schema.json"
DISCOVERY_SCHEMA_PATH = ROOT / "schemas" / "discovery.schema.json"
EXAMPLE_ENTRY_PATH = ROOT / "registry" / "examples" / "source-entry.json"
STATUS_SCHEMA_PATH = ROOT / "registry" / "schemas" / "source-status.schema.json"

CORE_CAPABILITIES = {"search", "detail", "catalog", "content"}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
REQUEST_TIMEOUT_SECONDS = 10.0


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class HttpResult:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes
    elapsed_ms: int

    def json(self) -> Any:
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RegistryError(f"{self.url} did not return valid UTF-8 JSON") from error


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned to a previously validated IP address."""

    def __init__(self, hostname: str, ip_address: str, port: int, timeout: float):
        super().__init__(hostname, port=port, timeout=timeout)
        self._pinned_ip = ip_address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._pinned_ip, self.port),
            self.timeout,
            self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
        except Exception:
            raw_socket.close()
            raise


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RegistryError(f"Cannot read JSON from {path}: {error}") from error


def json_validator(schema_path: Path) -> Draft202012Validator:
    return Draft202012Validator(
        load_json(schema_path),
        format_checker=FormatChecker(),
    )


def registry_validator() -> Draft202012Validator:
    source_schema = load_json(SOURCE_SCHEMA_PATH)
    schema_registry = Registry().with_resource(
        source_schema["$id"],
        Resource.from_contents(source_schema),
    )
    return Draft202012Validator(
        load_json(REGISTRY_SCHEMA_PATH),
        registry=schema_registry,
        format_checker=FormatChecker(),
    )


def format_validation_errors(
    validator: Draft202012Validator,
    value: Any,
) -> list[str]:
    errors = []
    for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def source_files() -> list[Path]:
    return sorted(SOURCES_DIR.glob("*.json"), key=lambda path: path.name.lower())


def validate_sources_directory() -> None:
    for path in SOURCES_DIR.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            raise RegistryError(f"Unexpected registry source entry: {path}")


def validate_manifest_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise RegistryError(f"Registry entry must be a regular file: {path}")
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise RegistryError(
            f"Registry entry exceeds {MAX_MANIFEST_BYTES} bytes: {path}"
        )


def validate_entries() -> list[dict[str, Any]]:
    validate_sources_directory()
    validator = json_validator(SOURCE_SCHEMA_PATH)
    entries: list[dict[str, Any]] = []
    ids: set[str] = set()
    failures: list[str] = []

    example = load_json(EXAMPLE_ENTRY_PATH)
    for message in format_validation_errors(validator, example):
        failures.append(f"{EXAMPLE_ENTRY_PATH.relative_to(ROOT)}: {message}")

    for path in source_files():
        validate_manifest_file(path)
        entry = load_json(path)
        errors = format_validation_errors(validator, entry)
        failures.extend(f"{path.relative_to(ROOT)}: {message}" for message in errors)
        if errors or not isinstance(entry, dict):
            continue
        source_id = entry["id"]
        if path.stem != source_id:
            failures.append(
                f"{path.relative_to(ROOT)}: filename must be {source_id}.json"
            )
        if source_id in ids:
            failures.append(f"{path.relative_to(ROOT)}: duplicate source ID {source_id}")
        ids.add(source_id)
        entries.append(entry)

    if failures:
        raise RegistryError("Registry validation failed:\n- " + "\n- ".join(failures))
    return sorted(entries, key=lambda entry: entry["id"])


def generated_document(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schemaVersion": "1.0", "sources": entries}


def validate_command(_: argparse.Namespace) -> None:
    entries = validate_entries()
    document = generated_document(entries)
    errors = format_validation_errors(registry_validator(), document)
    if errors:
        raise RegistryError("Generated registry is invalid:\n- " + "\n- ".join(errors))
    print(f"Registry static validation passed: {len(entries)} source(s)")


def build_command(args: argparse.Namespace) -> None:
    document = generated_document(validate_entries())
    errors = format_validation_errors(registry_validator(), document)
    if errors:
        raise RegistryError("Generated registry is invalid:\n- " + "\n- ".join(errors))
    encoded = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = GENERATED_REGISTRY.read_text(encoding="utf-8")
        if current != encoded:
            raise RegistryError(
                "registry/generated/registry.json is stale; run "
                "python scripts/registry_tool.py build"
            )
        print("Generated registry is up to date")
        return
    GENERATED_REGISTRY.write_text(encoded, encoding="utf-8", newline="\n")
    print(f"Built registry with {len(document['sources'])} source(s)")


def ensure_global_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    address = ipaddress.ip_address(value)
    if not address.is_global:
        raise RegistryError(f"Network target is not a public global IP: {address}")
    return address


def resolve_public_addresses(hostname: str, port: int) -> list[str]:
    try:
        records = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as error:
        raise RegistryError(f"Cannot resolve {hostname}: {error}") from error
    addresses: list[str] = []
    for record in records:
        value = record[4][0]
        ensure_global_ip(value)
        if value not in addresses:
            addresses.append(value)
    if not addresses:
        raise RegistryError(f"No public address found for {hostname}")
    return addresses


def validate_public_https_url(url: str) -> tuple[str, int, list[str]]:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise RegistryError(f"Only HTTPS registry targets are allowed: {url}")
    if not parsed.hostname or parsed.username or parsed.password:
        raise RegistryError(f"URL has an invalid authority: {url}")
    try:
        port = parsed.port or 443
    except ValueError as error:
        raise RegistryError(f"URL has an invalid port: {url}") from error
    return parsed.hostname, port, resolve_public_addresses(parsed.hostname, port)


def fetch(url: str) -> HttpResult:
    current_url = url
    for redirect_count in range(MAX_REDIRECTS + 1):
        parsed = urlsplit(current_url)
        hostname, port, addresses = validate_public_https_url(current_url)
        target = parsed.path or "/"
        if parsed.query:
            target += f"?{parsed.query}"
        started = time.monotonic()
        last_error: Exception | None = None
        response: http.client.HTTPResponse | None = None
        connection: PinnedHTTPSConnection | None = None
        for address in addresses:
            try:
                connection = PinnedHTTPSConnection(
                    hostname,
                    address,
                    port,
                    REQUEST_TIMEOUT_SECONDS,
                )
                connection.request(
                    "GET",
                    target,
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "identity",
                        "User-Agent": "ORSP-Registry-Validator/1.0",
                        "X-Open-Reading-Protocol": "1.4",
                    },
                )
                response = connection.getresponse()
                break
            except (OSError, ssl.SSLError, http.client.HTTPException) as error:
                last_error = error
                if connection is not None:
                    connection.close()
        if response is None or connection is None:
            raise RegistryError(f"Cannot connect to {current_url}: {last_error}")
        try:
            headers = {name.lower(): value for name, value in response.getheaders()}
            if response.status in REDIRECT_STATUSES:
                location = headers.get("location")
                response.read()
                if not location:
                    raise RegistryError(f"Redirect without Location from {current_url}")
                if redirect_count == MAX_REDIRECTS:
                    raise RegistryError(f"Too many redirects while fetching {url}")
                current_url = urljoin(current_url, location)
                continue
            body = response.read(MAX_JSON_BYTES + 1)
            if len(body) > MAX_JSON_BYTES:
                raise RegistryError(f"Response exceeds {MAX_JSON_BYTES} bytes: {current_url}")
            return HttpResult(
                current_url,
                response.status,
                headers,
                body,
                round((time.monotonic() - started) * 1000),
            )
        finally:
            connection.close()
    raise RegistryError(f"Too many redirects while fetching {url}")


def require_json(url: str, label: str) -> tuple[dict[str, Any], HttpResult]:
    result = fetch(url)
    if result.status != 200:
        raise RegistryError(f"{label} returned HTTP {result.status}: {result.url}")
    content_type = result.headers.get("content-type", "")
    if not content_type.lower().startswith("application/json"):
        raise RegistryError(f"{label} did not use application/json: {content_type}")
    value = result.json()
    if not isinstance(value, dict):
        raise RegistryError(f"{label} must return a JSON object")
    return value, result


def checked_api_url(api_base: str, relation: str, query: dict[str, str] | None = None) -> str:
    if not api_base.endswith("/"):
        raise RegistryError("Discovery apiBaseUrl must end in /")
    url = urljoin(api_base, relation)
    validate_public_https_url(url)
    if query:
        parsed = urlsplit(url)
        url = parsed._replace(query=urlencode(query)).geturl()
    return url


def require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 200:
        raise RegistryError(f"{label} is not a valid non-empty ID")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~-")
    if any(character not in allowed for character in value):
        raise RegistryError(f"{label} contains characters outside the ORSP ID alphabet")
    return value


def check_source(path: Path, profile: str = "core-reading") -> dict[str, Any]:
    validate_manifest_file(path)
    entry_validator = json_validator(SOURCE_SCHEMA_PATH)
    entry = load_json(path)
    errors = format_validation_errors(entry_validator, entry)
    if errors:
        raise RegistryError(f"Invalid source entry {path}:\n- " + "\n- ".join(errors))

    timings: dict[str, int] = {}
    stages: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    discovery, result = require_json(entry["discoveryUrl"], "Discovery")
    timings["discovery"] = result.elapsed_ms
    stages["discovery"] = {"status": "ok", "latencyMs": result.elapsed_ms}
    discovery_errors = format_validation_errors(
        json_validator(DISCOVERY_SCHEMA_PATH),
        discovery,
    )
    if discovery_errors:
        raise RegistryError("Invalid discovery document:\n- " + "\n- ".join(discovery_errors))
    if discovery["id"] != entry["id"]:
        raise RegistryError(
            f"Source ID mismatch: registry={entry['id']} discovery={discovery['id']}"
        )
    capabilities = set(discovery["capabilities"])
    if not CORE_CAPABILITIES.issubset(capabilities):
        missing = ", ".join(sorted(CORE_CAPABILITIES - capabilities))
        raise RegistryError(f"Discovery is missing core capabilities: {missing}")
    discovery_languages = set(discovery.get("languages", []))
    declared_languages = set(entry["languages"])
    if discovery_languages and not declared_languages.issubset(discovery_languages):
        warnings.append("Registry languages are not all declared by discovery")

    api_base = discovery["apiBaseUrl"]
    if profile == "discovery":
        required = {"discover", "categories", "browse"}
        if not required.issubset(capabilities):
            missing = ", ".join(sorted(required - capabilities))
            raise RegistryError(f"Discovery profile is missing capabilities: {missing}")
        discover, result = require_json(checked_api_url(api_base, "v1/discover"), "Discover")
        timings["discover"] = result.elapsed_ms
        sections = discover.get("sections")
        if not isinstance(sections, list) or not any(
            isinstance(section, dict) and isinstance(section.get("items"), list) and section["items"]
            for section in sections
        ):
            raise RegistryError("Discover did not return a non-empty section")
        stages["discover"] = {"status": "ok", "latencyMs": result.elapsed_ms}

        categories, result = require_json(checked_api_url(api_base, "v1/categories"), "Categories")
        timings["categories"] = result.elapsed_ms
        category_items = categories.get("items")
        if not isinstance(category_items, list) or not category_items or not isinstance(category_items[0], dict):
            raise RegistryError("Categories did not return a browseable category")
        category_id = require_id(category_items[0].get("id"), "Category ID")
        stages["categories"] = {"status": "ok", "latencyMs": result.elapsed_ms}

        browse, result = require_json(
            checked_api_url(api_base, "v1/browse", {"category": category_id, "page": "1", "pageSize": "1"}),
            "Browse",
        )
        timings["browse"] = result.elapsed_ms
        browse_items = browse.get("items")
        if not isinstance(browse_items, list) or not browse_items:
            raise RegistryError("Browse did not return a book for the declared category")
        stages["browse"] = {"status": "ok", "latencyMs": result.elapsed_ms}
        return diagnostic_report(entry["id"], profile, discovery["protocolVersion"], stages, warnings)

    search_url = checked_api_url(
        api_base,
        "v1/search",
        {"q": entry["testQuery"], "page": "1", "pageSize": "1"},
    )
    search, result = require_json(search_url, "Search")
    timings["search"] = result.elapsed_ms
    stages["search"] = {"status": "ok", "latencyMs": result.elapsed_ms}
    search_items = search.get("items")
    if not isinstance(search_items, list) or not search_items:
        raise RegistryError("testQuery did not return a book")
    first_book = search_items[0]
    if not isinstance(first_book, dict):
        raise RegistryError("Search item must be an object")
    book_id = require_id(first_book.get("id"), "Search book ID")

    detail_url = checked_api_url(api_base, f"v1/books/{quote(book_id, safe='')}")
    detail, result = require_json(detail_url, "Book detail")
    timings["detail"] = result.elapsed_ms
    stages["detail"] = {"status": "ok", "latencyMs": result.elapsed_ms}
    if detail.get("id") != book_id:
        raise RegistryError("Book detail ID does not match the search result")

    catalog_url = checked_api_url(
        api_base,
        f"v1/books/{quote(book_id, safe='')}/chapters",
        {"page": "1", "pageSize": "1"},
    )
    catalog, result = require_json(catalog_url, "Chapter catalog")
    timings["catalog"] = result.elapsed_ms
    stages["catalog"] = {"status": "ok", "latencyMs": result.elapsed_ms}
    chapter_items = catalog.get("items")
    if not isinstance(chapter_items, list) or not chapter_items:
        raise RegistryError("The selected test book has no chapter")
    first_chapter = chapter_items[0]
    if not isinstance(first_chapter, dict):
        raise RegistryError("Chapter item must be an object")
    chapter_id = require_id(first_chapter.get("id"), "Chapter ID")

    content_url = checked_api_url(
        api_base,
        f"v1/books/{quote(book_id, safe='')}/chapters/{quote(chapter_id, safe='')}",
    )
    content, result = require_json(content_url, "Chapter content")
    timings["content"] = result.elapsed_ms
    stages["content"] = {"status": "ok", "latencyMs": result.elapsed_ms}
    if content.get("bookId") != book_id or content.get("chapterId") != chapter_id:
        raise RegistryError("Chapter content IDs do not match the requested resource")
    if content.get("contentType") not in {"text/plain", "text/markdown", "text/html"}:
        raise RegistryError("Chapter contentType is not supported by ORSP 1.4")
    if not isinstance(content.get("content"), str):
        raise RegistryError("Chapter content must be a string")

    return diagnostic_report(entry["id"], profile, discovery["protocolVersion"], stages, warnings)


def diagnostic_report(
    source_id: str,
    profile: str,
    protocol_version: str,
    stages: dict[str, dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    report = {
        "schemaVersion": "1.0",
        "id": source_id,
        "status": "verified",
        "profile": profile,
        "protocolVersion": protocol_version,
        "checkedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stages": stages,
        "warnings": warnings,
    }
    errors = format_validation_errors(json_validator(STATUS_SCHEMA_PATH), report)
    if errors:
        raise RegistryError("Generated diagnostic record is invalid:\n- " + "\n- ".join(errors))
    return report


def check_source_command(args: argparse.Namespace) -> None:
    report = check_source(Path(args.entry).absolute(), args.profile)
    if args.status_output:
        Path(args.status_output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


def check_all_command(args: argparse.Namespace) -> None:
    reports: list[dict[str, Any]] = []
    failures = 0
    for path in source_files():
        try:
            reports.append(check_source(path))
        except RegistryError as error:
            failures += 1
            reports.append(
                {
                    "id": path.stem,
                    "status": "offline",
                    "checkedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "error": str(error),
                }
            )
    output = {
        "schemaVersion": "1.0",
        "checkedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources": reports,
    }
    if args.status_output:
        Path(args.status_output).write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if failures:
        raise RegistryError(f"Network validation failed for {failures} source(s)")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate source manifests")
    validate.set_defaults(function=validate_command)

    build = commands.add_parser("build", help="build the combined registry")
    build.add_argument("--check", action="store_true", help="fail if output is stale")
    build.set_defaults(function=build_command)

    check_source_parser = commands.add_parser(
        "check-source",
        help="safely test one source over the network",
    )
    check_source_parser.add_argument("entry", help="path to a source entry JSON file")
    check_source_parser.add_argument("--status-output")
    check_source_parser.add_argument("--profile", choices=["core-reading", "discovery"], default="core-reading")
    check_source_parser.set_defaults(function=check_source_command)

    check_all = commands.add_parser(
        "check-all",
        help="safely test every accepted source over the network",
    )
    check_all.add_argument("--status-output")
    check_all.set_defaults(function=check_all_command)
    return value


def main() -> None:
    args = parser().parse_args()
    try:
        args.function(args)
    except RegistryError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
