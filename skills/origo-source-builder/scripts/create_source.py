"""Create a local text source without overwriting an existing project."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def contract_root():
    packaged = SKILL / "references/orsp"
    return packaged if packaged.is_dir() else SKILL.parent.parent


def create_source(destination, source_id, name):
    schema = json.loads(
        (contract_root() / "schemas/discovery.schema.json").read_text(encoding="utf-8")
    )
    for key, value in (("id", source_id), ("name", name)):
        rule = schema["properties"][key]
        if not rule["minLength"] <= len(value) <= rule["maxLength"] or (
            "pattern" in rule and not re.fullmatch(rule["pattern"], value)
        ):
            raise ValueError(f"Invalid source {key}")
    if not name.strip():
        raise ValueError("Source name must not be blank")
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(
            "Destination exists; choose a new directory or adapt the existing project"
        )
    files = json.loads(
        (SKILL / "references/contract-files.json").read_text(encoding="utf-8")
    )
    for filename in files:
        if not (contract_root() / filename).is_file():
            raise FileNotFoundError(f"Missing bundled contract: {filename}")
    destination.mkdir(parents=True)
    for filename in ("server.py", "library.py"):
        shutil.copyfile(SKILL / "assets" / filename, destination / filename)
    for filename in files:
        target = destination / "contract" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(contract_root() / filename, target)
    (destination / "contract/requirements.txt").write_text(
        "jsonschema>=4.26,<5\nPyYAML>=6,<7\nopenapi-spec-validator>=0.9,<1\n",
        encoding="utf-8",
    )
    library = {
        "id": source_id,
        "name": name,
        "books": [
            {
                "id": "original-book",
                "title": "Give reading a little time",
                "author": "Original sample",
                "chapters": [
                    {
                        "id": "first-page",
                        "title": "First page",
                        "order": 0,
                        "content": "A short original sample. Replace it with your own writing.",
                    },
                    {
                        "id": "second-page",
                        "title": "Second page",
                        "order": 1,
                        "content": "Keep each chapter identity stable when revising its words.",
                    },
                ],
            }
        ],
    }
    (destination / "library.json").write_text(
        json.dumps(library, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destination / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n.venv/\n.env\n", encoding="utf-8"
    )
    (destination / "README.md").write_text(
        "# "
        + name
        + "\n\nAn independent Origo Source using ORSP 1.6 candidate. Python 3.11+.\n\n"
        "```sh\npython server.py --port 8787\npython -m pip install -r contract/requirements.txt\n"
        "python contract/scripts/probe_source.py http://127.0.0.1:8787/.well-known/origo-source.json --allow-loopback\n```\n\n"
        "Core text reading, browse and chapter updates are implemented. Update library.json atomically; do not change published IDs.\n"
        "Storage lives in library.py; HTTP lives in server.py. The file limit is 8 MiB. For a requested proxy deployment use "
        "`--public-origin https://books.example.org`. Direct HTTPS uses `--tls-cert /secure/fullchain.pem --tls-key /secure/private.pem` together. "
        "Public HTTPS is recommended; local HTTP remains supported. New discovery is `/.well-known/origo-source.json`; the old discovery alias remains available for installed readers. "
        "Keep content outside immutable code releases.\n\n"
        "Other profiles need implementation before declaration. Bundled reference checks validate the contract fixtures, not this service.\n",
        encoding="utf-8",
    )
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--id", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        destination = create_source(args.destination, args.id, args.name)
    except (ValueError, FileExistsError, FileNotFoundError) as error:
        parser.error(str(error))
    print(f"Created source at {destination}; run python server.py from that directory")


if __name__ == "__main__":
    main()
