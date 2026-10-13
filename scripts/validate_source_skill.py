"""Exercise the downloadable Skill: scaffold, real HTTP, updates and provenance."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

from build_source_skill import ROOT, build
from probe_source import Transport, probe
from reading_contracts import Contracts


def main():
    data, receipt = build(worktree=True)
    assert data == build(worktree=True)[0], "Bundle must be deterministic"
    contracts = Contracts()
    checks = 0

    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(label)

    temporary_root = ROOT / "build"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="source-skill-", dir=temporary_root
    ) as directory:
        root = Path(directory)
        with ZipFile(io.BytesIO(data)) as archive:
            for member in archive.infolist():
                assert (root / member.filename).resolve().is_relative_to(root.resolve())
            archive.extractall(root)
        skill = root / "origo-source-builder"
        manifest = json.loads(
            (skill / "references/bundle-manifest.json").read_text(encoding="utf-8")
        )
        for filename, expected in manifest["files"].items():
            check(
                hashlib.sha256((skill / filename).read_bytes()).hexdigest()
                == expected["sha256"],
                "Bundled resource integrity",
            )
        check(
            manifest["protocolVersion"] == receipt["protocolVersion"],
            "Bundle version provenance",
        )
        project = root / "my-source"
        command = [
            sys.executable,
            str(skill / "scripts/create_source.py"),
            str(project),
            "--id",
            "org.example.skill-test",
            "--name",
            "原创试验书源",
        ]
        subprocess.run(command, check=True, capture_output=True)
        before = (project / "library.json").read_bytes()
        existing = subprocess.run(command, capture_output=True, check=False)
        check(
            existing.returncode != 0
            and (project / "library.json").read_bytes() == before,
            "Existing projects are never overwritten",
        )
        sys.path.insert(0, str(project))
        spec = importlib.util.spec_from_file_location(
            "skill_starter_server", project / "server.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        server = module.create_server(project / "library.json", port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def get(path, status=200, headers=None):
            try:
                response = urlopen(
                    Request(base + path, headers=headers or {}), timeout=5
                )
            except HTTPError as error:
                response = error
            with response:
                check(response.status == status, "Expected HTTP status")
                raw = response.read()
                return json.loads(raw) if raw else None, response.headers

        def replace(value):
            incoming = project / "library.incoming"
            incoming.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            incoming.replace(project / "library.json")

        try:
            discovery, _ = get("/.well-known/open-reading-source.json")
            contracts.validator("discovery").validate(discovery)
            report = probe(
                base + "/.well-known/open-reading-source.json",
                transport=Transport(allow_loopback=True),
            )
            check(
                not report["issues"]
                and all(not item["issues"] for item in report["checks"]),
                "Generated source passes actual HTTP probe",
            )
            book = "/api/v1/books/original-book"
            first, etags = get(book + "/updates")
            contracts.validator("updates", "UpdateState").validate(first)
            get(book + "/updates", 304, {"If-None-Match": etags["ETag"]})
            library = json.loads(before)
            library["books"][0]["chapters"][0]["content"] = (
                "修订后的原创文字，章节数量保持不变。"
            )
            replace(library)
            changed, _ = get(book + "/updates")
            check(
                changed["chapterCount"] == first["chapterCount"]
                and changed["catalogVersion"] != first["catalogVersion"],
                "Same-count body edit invalidates snapshot",
            )
            get(
                book + "/chapters?catalogVersion=" + first["catalogVersion"],
                409,
                {"If-None-Match": "*"},
            )
            content, _ = get(book + "/chapters/first-page")
            check(
                content["contentVersion"]
                == hashlib.sha256(content["content"].encode()).hexdigest(),
                "Exact Unicode UTF-8 text version",
            )
            library["books"][0]["chapters"].append(
                {
                    "id": "third-page",
                    "title": "Third",
                    "content": "An original third chapter.",
                }
            )
            replace(library)
            added, _ = get(book + "/updates")
            check(
                added["chapterCount"] == 3
                and added["latestChapter"]["id"] == "third-page",
                "Appended chapter appears",
            )
            page, _ = get(
                book
                + "/chapters?page=2&pageSize=1&catalogVersion="
                + added["catalogVersion"]
            )
            contracts.validator("updates", "Catalog").validate(page)
            check(
                page["items"][0]["id"] == "second-page", "Pinned pagination is ordered"
            )
            library["books"][0]["chapters"].pop(0)
            replace(library)
            deleted, _ = get(book + "/updates")
            check(
                deleted["chapterCount"] == 2
                and deleted["catalogVersion"] != added["catalogVersion"],
                "Deletion invalidates catalog",
            )
            get(book + "/chapters?pageSize=201", 400)
            get(book + "/chapters/absent", 404)
            check(
                module.public_origin("https://books.example.org/")
                == "https://books.example.org",
                "Configured public origin",
            )
            for invalid_origin in (
                "https://secret@books.example.org",
                "file:///private",
                "https://books.example.org/private",
                "https://books.example.org?token=secret",
            ):
                try:
                    module.public_origin(invalid_origin)
                except ValueError:
                    check(True, "Unsafe public origin rejected")
                else:
                    raise AssertionError("Invalid public origin accepted")
            library["id"] = "changed-source-id"
            replace(library)
            get("/.well-known/open-reading-source.json", 503)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            sys.path.pop(0)
    print(
        f"Source builder Skill validation passed: {checks} checks; scaffold and actual HTTP verified"
    )


if __name__ == "__main__":
    main()
