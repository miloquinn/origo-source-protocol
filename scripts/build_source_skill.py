"""Package a deterministic, self-contained source Skill from a pinned Git commit."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "skills/origo-source-builder/"
SKILL_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/architecture.md",
    "references/contract-files.json",
    "scripts/create_source.py",
    "assets/library.py",
    "assets/server.py",
)


def build(*, ref="HEAD", worktree=False):
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", ref + "^{commit}"], cwd=ROOT, text=True
    ).strip()

    def read(path):
        if worktree:
            return (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        return subprocess.check_output(
            ["git", "show", commit + ":" + path], cwd=ROOT
        ).replace(b"\r\n", b"\n")

    files = {name: read(PREFIX + name) for name in SKILL_FILES}
    paths = json.loads(files["references/contract-files.json"])
    for path in paths:
        if path.startswith("/") or ".." in Path(path).parts:
            raise ValueError("Invalid contract resource path")
        files["references/orsp/" + path] = read(path)
    version = json.loads(read("examples/open-reading-source.json"))["protocolVersion"]
    starter_version = re.search(
        rb'PROTOCOL_VERSION = "([0-9]+\.[0-9]+)"', files["assets/server.py"]
    )[1].decode()
    if starter_version != version:
        raise ValueError("Starter and canonical protocol versions differ")
    receipt = {
        "schemaVersion": 1,
        "name": "origo-source-builder",
        "brand": "Origo Source",
        "chineseName": "元源",
        "protocol": "open-reading-source",
        "protocolVersion": version,
        "protocolStatus": "candidate",
        "sourceRepository": "https://github.com/miloquinn/origo-source-protocol",
        "sourceCommit": commit,
        "developmentSnapshot": worktree,
        "files": {
            path: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for path, data in sorted(files.items())
        },
    }
    files["references/bundle-manifest.json"] = (
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    stream = io.BytesIO()
    with ZipFile(stream, "w") as archive:
        for path, data in sorted(files.items()):
            info = ZipInfo(
                "origo-source-builder/" + path, date_time=(1980, 1, 1, 0, 0, 0)
            )
            info.create_system = 3
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    data = stream.getvalue()
    return data, {
        **receipt,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument(
        "--worktree", action="store_true", help="Local validation only; not publishable"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "dist/origo-source-builder.zip"
    )
    args = parser.parse_args()
    data, receipt = build(ref=args.ref, worktree=args.worktree)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    args.output.with_suffix(".json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Built {len(data)} bytes; SHA-256 {receipt['sha256']}; source {receipt['sourceCommit']}"
    )


if __name__ == "__main__":
    main()
