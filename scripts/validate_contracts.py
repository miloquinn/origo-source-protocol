"""Validate ORSP machine-readable contracts and compatibility invariants."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate_spec


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> object:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def expect_invalid(validator: Draft202012Validator, value: object, name: str) -> None:
    if validator.is_valid(value):
        raise AssertionError(f"Expected invalid discovery fixture: {name}")


def main() -> None:
    schema = load_json("schemas/discovery.schema.json")
    discovery = load_json("examples/open-reading-source.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(discovery)

    legacy_optional = copy.deepcopy(discovery)
    legacy_optional["protocolVersion"] = "1.4"
    legacy_optional["supportedVersions"] = ["1.4"]
    legacy_optional["capabilities"].remove("rankings")
    validator.validate(legacy_optional)

    extension_fixture = copy.deepcopy(discovery)
    extension_fixture["capabilities"].append("org.example:audio")
    validator.validate(extension_fixture)

    patch_version = copy.deepcopy(discovery)
    patch_version["protocolVersion"] = "1.0.0"
    expect_invalid(validator, patch_version, "patch protocol version")

    missing_core = copy.deepcopy(discovery)
    missing_core["capabilities"].remove("content")
    expect_invalid(validator, missing_core, "missing core capability")

    categories_without_browse = copy.deepcopy(discovery)
    categories_without_browse["capabilities"].remove("browse")
    expect_invalid(
        validator,
        categories_without_browse,
        "categories capability without browse",
    )

    no_trailing_slash = copy.deepcopy(discovery)
    no_trailing_slash["apiBaseUrl"] = "https://books.example.org/api"
    expect_invalid(validator, no_trailing_slash, "API URL without trailing slash")

    api_user_info = copy.deepcopy(discovery)
    api_user_info["apiBaseUrl"] = "https://user@books.example.org/api/"
    expect_invalid(validator, api_user_info, "API URL containing user information")

    reserved_extension = copy.deepcopy(discovery)
    reserved_extension["capabilities"].append("orsp:private")
    expect_invalid(validator, reserved_extension, "reserved extension namespace")

    patch_supported_version = copy.deepcopy(discovery)
    patch_supported_version["supportedVersions"] = ["1.3.0"]
    expect_invalid(
        validator,
        patch_supported_version,
        "patch version inside supportedVersions",
    )

    catalog_page_size_too_small = copy.deepcopy(discovery)
    catalog_page_size_too_small["maxCatalogPageSize"] = 0
    expect_invalid(
        validator,
        catalog_page_size_too_small,
        "maxCatalogPageSize below the shared minimum",
    )

    catalog_page_size_too_large = copy.deepcopy(discovery)
    catalog_page_size_too_large["maxCatalogPageSize"] = 5000
    expect_invalid(
        validator,
        catalog_page_size_too_large,
        "maxCatalogPageSize above the shared maximum",
    )

    openapi = yaml.safe_load((ROOT / "openapi.yaml").read_text(encoding="utf-8"))
    validate_spec(openapi)

    print("ORSP contract validation passed")


if __name__ == "__main__":
    main()
