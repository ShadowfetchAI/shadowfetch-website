#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib import request


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DEFAULT_ORIGIN = "https://www.shadowfetch.com"
USER_AGENT = "ShadowfetchSiteCheck/2.0 (+https://www.shadowfetch.com)"


def fetch(url: str) -> tuple[int, str]:
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    with request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def check_local() -> list[str]:
    failures: list[str] = []
    index_path = DIST / "index.html"
    if not index_path.exists():
        failures.append("dist/index.html is missing")
        return failures

    html = index_path.read_text(encoding="utf-8")
    if "Engineering the Next Generation of Intelligence." not in html:
      failures.append("dist/index.html is missing the new hero headline")
    if 'data-edition="studio"' not in html:
        failures.append("dist/index.html is missing the studio edition marker")

    required = (
        "manifest.webmanifest",
        "robots.txt",
        "service-worker.js",
        "assets/styles.css",
        "assets/app.js",
        "assets/shadowfetch-mark.svg",
        "assets/shadowfetch-crest.jpg",
        "signup/index.html",
    )
    for rel_path in required:
        if not (DIST / rel_path).exists():
            failures.append(f"dist/{rel_path} is missing")
    return failures


def check_live(origin: str) -> list[str]:
    failures: list[str] = []
    try:
        status, html = fetch(f"{origin}/")
        if status != 200:
            failures.append(f"homepage returned HTTP {status}")
        if "Engineering the Next Generation of Intelligence." not in html:
            failures.append("live homepage is not serving the new Shadowfetch front-end")
    except Exception as exc:
        failures.append(f"homepage check failed: {exc}")
    return failures


def parse_origin(argv: list[str]) -> str | None:
    if len(argv) <= 1:
        return None
    if argv[1] == "--live":
        return argv[2] if len(argv) > 2 else DEFAULT_ORIGIN
    return argv[1]


def main(argv: list[str]) -> int:
    failures = check_local()
    origin = parse_origin(argv)
    checks = ["local build"]
    if origin:
        failures.extend(check_live(origin))
        checks.append(f"live homepage ({origin})")

    if failures:
        print(json.dumps({"ok": False, "failures": failures}, indent=2))
        return 1

    print(json.dumps({"ok": True, "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
