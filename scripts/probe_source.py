"""Read-only, bounded ORSP source inspection; reports structure, never book bodies."""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import socket
from datetime import UTC, datetime
from urllib.parse import quote, urlencode, urljoin, urlsplit

from reading_contracts import Contracts, media_issues, strict_json
from registry_tool import PinnedHTTPSConnection, RegistryError, resolve_public_addresses

REDIRECTS = {301, 302, 303, 307, 308}


class ProbeError(RuntimeError):
    pass


class Transport:
    def __init__(self, *, allow_loopback=False):
        self.allow_loopback = allow_loopback
        self.requests = 0

    def addresses(self, parsed):
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ProbeError("Only absolute HTTP(S) URLs are supported")
        if parsed.username is not None or parsed.password is not None:
            raise ProbeError("URLs containing credentials are forbidden")
        if any(char.isspace() for char in parsed.geturl()):
            raise ProbeError("Whitespace in URL is forbidden")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if self.allow_loopback and parsed.hostname in ("127.0.0.1", "::1", "localhost"):
            records = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
            addresses = list(dict.fromkeys(record[4][0] for record in records))
            if not addresses or not all(
                ipaddress.ip_address(a).is_loopback for a in addresses
            ):
                raise ProbeError("Local fixture did not resolve to loopback")
        else:
            addresses = resolve_public_addresses(parsed.hostname, port)
        return port, addresses

    def get(self, url, *, limit=1024 * 1024):
        for _ in range(4):
            self.requests += 1
            if self.requests > 20:
                raise ProbeError("Request budget exceeded")
            parsed = urlsplit(url)
            port, addresses = self.addresses(parsed)
            if parsed.scheme == "https":
                connection = PinnedHTTPSConnection(
                    parsed.hostname, addresses[0], port, 12
                )
            else:
                connection = http.client.HTTPConnection(addresses[0], port, timeout=12)
            authority = parsed.netloc
            try:
                connection.request(
                    "GET",
                    (parsed.path or "/") + ("?" + parsed.query if parsed.query else ""),
                    headers={
                        "Host": authority,
                        "Accept": "application/json",
                        "Accept-Encoding": "identity",
                        "User-Agent": "ORSP-Source-Probe/1.0",
                        "X-Origo-Source-Protocol": "1.6",
                        "X-Origo-Source-Request-Purpose": "health-check",
                        "X-Open-Reading-Protocol": "1.6",
                        "X-Open-Reading-Request-Purpose": "health-check",
                    },
                )
                response = connection.getresponse()
                headers = {key.lower(): value for key, value in response.getheaders()}
                if response.status in REDIRECTS:
                    location = headers.get("location")
                    if not location:
                        raise ProbeError("Redirect is missing Location")
                    next_url = urljoin(url, location)
                    if (
                        parsed.scheme == "https"
                        and urlsplit(next_url).scheme != "https"
                    ):
                        raise ProbeError("HTTPS downgrade redirect is forbidden")
                    url = next_url
                    continue
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise ProbeError("Response size limit exceeded")
                return response.status, headers, data
            finally:
                connection.close()
        raise ProbeError("Redirect limit exceeded")


def probe(discovery_url, *, transport=None):
    transport = transport or Transport()
    contracts = Contracts()
    report = {"checkedAt": datetime.now(UTC).isoformat(), "checks": [], "issues": []}

    def read(label, url, profile, model=None):
        check = {"endpoint": label}
        report["checks"].append(check)
        try:
            status, headers, data = transport.get(
                url, limit=65536 if label == "discovery" else 1048576
            )
            check["status"] = status
            if status != 200:
                raise ProbeError(f"Expected HTTP 200, received {status}")
            if (
                headers.get("content-type", "").split(";", 1)[0].lower()
                != "application/json"
            ):
                raise ProbeError("Expected application/json")
            body = strict_json(data.decode("utf-8"))
            if not isinstance(body, dict):
                raise ProbeError("Expected a JSON object")
            check["fields"] = sorted(body)
            check["issues"] = contracts.issues(profile, model, body)
            check["etag"] = bool(headers.get("etag"))
            return body if not check["issues"] or model == "ChapterContent" else None
        except (
            ProbeError,
            RegistryError,
            OSError,
            http.client.HTTPException,
            ValueError,
        ) as error:
            check["issues"] = [
                str(error)
                if isinstance(error, ProbeError)
                else "Network policy or name resolution rejected this target"
                if isinstance(error, RegistryError)
                else type(error).__name__
            ]
            return None

    manifest = read("discovery", discovery_url, "discovery")
    if not manifest or report["checks"][-1]["issues"]:
        report["issues"] = ["Discovery validation failed; no API requests were made"]
        return report
    report["source"] = {
        key: manifest[key] for key in ("id", "protocolVersion", "capabilities")
    }
    report["source"]["contentTypes"] = manifest.get("contentTypes", [])
    base, capabilities = manifest["apiBaseUrl"], set(manifest["capabilities"])

    def api(path, profile="core", model=None):
        return read(path.split("?", 1)[0], urljoin(base, path), profile, model)

    candidate = None
    if "browse" in capabilities:
        page = api("v1/browse?page=1&pageSize=1", model="SearchPage")
        if page and page.get("items"):
            candidate = page["items"][0]
    title = (
        candidate.get("title", "reading") if isinstance(candidate, dict) else "reading"
    )
    search = api(
        "v1/search?" + urlencode({"q": title[:200], "pageSize": 1}), model="SearchPage"
    )
    if candidate is None and search and search.get("items"):
        candidate = search["items"][0]
    if "categories" in capabilities:
        api("v1/categories", model="CategoryPage")
    if "discover" in capabilities:
        shelves = api("v1/discover", model="DiscoveryPage")
        if candidate is None and shelves:
            candidate = next(
                (
                    section["items"][0]
                    for section in shelves.get("sections", [])
                    if section.get("items")
                ),
                None,
            )
    if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
        book_id = candidate["id"]
        path = "v1/books/" + quote(book_id, safe="")
        detail = api(path, model="Book")
        if detail and detail.get("id") != book_id:
            report["checks"][-1]["issues"].append("Book ID does not match request")
        catalog = api(path + "/chapters?page=1&pageSize=1", model="ChapterPage")
        if catalog and catalog.get("items"):
            chapter = catalog["items"][0]
            if isinstance(chapter, dict) and isinstance(chapter.get("id"), str):
                content = api(
                    path + "/chapters/" + quote(chapter["id"], safe=""),
                    model="ChapterContent",
                )
                if content:
                    check = report["checks"][-1]
                    if (
                        content.get("bookId") != book_id
                        or content.get("chapterId") != chapter["id"]
                    ):
                        check["issues"].append("Content IDs do not match request")
                    check["contentType"] = content.get("contentType")
                    check["contentCharacters"] = (
                        len(content.get("content", ""))
                        if isinstance(content.get("content"), str)
                        else None
                    )
                    if "title" not in content:
                        check["issues"].append(
                            "Required title is missing; existing Origo X can use the catalog title"
                        )
                    check["issues"].extend(media_issues(manifest, content))

        else:
            report["issues"].append(
                "No chapter sampled; content compatibility is inconclusive"
            )
        if "top.xxread:chapter-updates" in capabilities:
            api(path + "/updates", "updates", "UpdateState")
        if "top.xxread:publications" in capabilities:
            api(path + "/publications", "publications", "Publications")
    else:
        report["issues"].append(
            "No book sampled; reading compatibility is inconclusive"
        )
    if "rankings" in capabilities:
        rankings = api("v1/rankings", model="RankingCollection")
        if rankings and rankings.get("items"):
            ranking = rankings["items"][0]
            if isinstance(ranking, dict) and isinstance(ranking.get("id"), str):
                page = api(
                    "v1/rankings/" + quote(ranking["id"], safe="") + "?pageSize=1",
                    model="RankingPage",
                )
                if page and page.get("ranking", {}).get("id") != ranking["id"]:
                    report["checks"][-1]["issues"].append(
                        "Ranking ID does not match request"
                    )
    report["limitations"] = [
        "One book/chapter and one ranking page were sampled; advertised capabilities are not full acceptance.",
        "No media bytes downloaded, no write requests, no credentials, and no book bodies retained.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("discovery_url")
    parser.add_argument(
        "--allow-loopback",
        action="store_true",
        help="Permit local reference fixtures only",
    )
    args = parser.parse_args()
    result = probe(
        args.discovery_url, transport=Transport(allow_loopback=args.allow_loopback)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(
        bool(result["issues"] or any(check.get("issues") for check in result["checks"]))
    )


if __name__ == "__main__":
    raise SystemExit(main())
