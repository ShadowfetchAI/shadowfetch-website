#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
THEME_COLOR = "#111111"


def compute_asset_version() -> str:
    digest = hashlib.sha1()
    for relative_path in ("assets/styles.css", "assets/app.js", "assets/shadowfetch-mark.svg", "assets/shadowfetch-bible-logo.png"):
        digest.update((ROOT / relative_path).read_bytes())
    return digest.hexdigest()[:12]


ASSET_VERSION = compute_asset_version()

DIRECTORIES = [
    "about",
    "archive",
    "assets",
    "bible",
    "calendar",
    "settings",
    "signup",
]

FILES = [
    "index.html",
    "manifest.webmanifest",
    "robots.txt",
    "service-worker.js",
]

HEADERS_CONTENT = """\
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN

/assets/*
  Cache-Control: public, max-age=3600

/assets/data/*
  Cache-Control: public, max-age=900

/feed.xml
  Cache-Control: public, max-age=900
"""

NOT_FOUND_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Not Found | Shadowfetch Bible Edition</title>
  <meta name="description" content="The page you were looking for was not found.">
  <meta name="theme-color" content="#1a1a1a">
  <link rel="stylesheet" href="/assets/styles.css?v=""" + ASSET_VERSION + """">
</head>
<body data-edition="bible" data-page="not-found">
  <main class="container" style="padding: 5rem 0; text-align: center;">
    <p style="font-family: ‘IBM Plex Sans’, sans-serif; font-size: 0.75rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--accent); margin: 0 0 1rem;">Shadowfetch &bull; Bible Edition</p>
    <h1 style="font-family: ‘Cormorant Garamond’, Georgia, serif; font-size: 2.5rem; margin: 0 0 1rem;">This page was not found.</h1>
    <p style="font-size: 1.1rem; color: var(--muted); margin: 0 0 2rem;">"He who dwells in the shelter of the Most High will abide in the shadow of the Almighty." &mdash; Psalm 91:1</p>
    <a href="/" style="display: inline-block; padding: 0.75rem 1.5rem; background: var(--accent); color: #fff7ed; font-family: ‘IBM Plex Sans’, sans-serif; font-size: 0.85rem; letter-spacing: 0.08em; text-transform: uppercase; text-decoration: none;">Return to Today&rsquo;s Reading</a>
  </main>
</body>
</html>
"""


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)

    DIST.mkdir(parents=True, exist_ok=True)

    for directory in DIRECTORIES:
        source = ROOT / directory
        if source.exists():
            shutil.copytree(source, DIST / directory)

    for filename in FILES:
        source = ROOT / filename
        if source.exists():
            shutil.copy2(source, DIST / filename)

    (DIST / "_headers").write_text(HEADERS_CONTENT, encoding="utf-8")
    (DIST / "404.html").write_text(NOT_FOUND_HTML, encoding="utf-8")


if __name__ == "__main__":
    main()
