#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
THEME_COLOR = "#05070A"


def compute_asset_version() -> str:
    digest = hashlib.sha1()
    for relative_path in ("assets/styles.css", "assets/app.js", "assets/shadowfetch-mark.svg", "assets/shadowfetch-crest.jpg"):
        digest.update((ROOT / relative_path).read_bytes())
    return digest.hexdigest()[:12]


ASSET_VERSION = compute_asset_version()

DIRECTORIES = [
    "assets",
    "arbiter",
    "archive",
    "bible",
    "blessed",
    "calendar",
    "daily-word-journey",
    "fast-pdf",
    "grandmas-cookbook",
    "hush",
    "receipt-to-pdf",
    "renew-guard",
    "route-pay",
    "snapdeck",
    "shift-swap-liaison",
    "settings",
    "shadowfetch",
    "signup",
    "text-cleanse",
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

/
  Cache-Control: public, max-age=0, must-revalidate

/arbiter/
  Cache-Control: public, max-age=0, must-revalidate

/bible/
  Cache-Control: public, max-age=0, must-revalidate

/archive/
  Cache-Control: public, max-age=0, must-revalidate

/blessed/
  Cache-Control: public, max-age=0, must-revalidate

/calendar/
  Cache-Control: public, max-age=0, must-revalidate

/daily-word-journey/
  Cache-Control: public, max-age=0, must-revalidate

/fast-pdf/
  Cache-Control: public, max-age=0, must-revalidate

/grandmas-cookbook/
  Cache-Control: public, max-age=0, must-revalidate

/hush/
  Cache-Control: public, max-age=0, must-revalidate

/receipt-to-pdf/
  Cache-Control: public, max-age=0, must-revalidate

/renew-guard/
  Cache-Control: public, max-age=0, must-revalidate

/route-pay/
  Cache-Control: public, max-age=0, must-revalidate

/snapdeck/
  Cache-Control: public, max-age=0, must-revalidate

/shift-swap-liaison/
  Cache-Control: public, max-age=0, must-revalidate

/settings/
  Cache-Control: public, max-age=0, must-revalidate

/shadowfetch/
  Cache-Control: public, max-age=0, must-revalidate

/signup/
  Cache-Control: public, max-age=0, must-revalidate

/text-cleanse/
  Cache-Control: public, max-age=0, must-revalidate

/service-worker.js
  Cache-Control: public, max-age=0, must-revalidate

/assets/*
  Cache-Control: public, max-age=3600

/assets/data/*
  Cache-Control: public, max-age=900

/feed.xml
  Cache-Control: public, max-age=900
"""


def build_redirects_content() -> str:
    redirect_lines: list[str] = []

    for index_file in sorted(DIST.rglob("index.html")):
        relative_parent = index_file.parent.relative_to(DIST)
        if str(relative_parent) == ".":
            continue

        source_path = "/" + relative_parent.as_posix()
        destination_path = source_path + "/"
        redirect_lines.append(f"{source_path} {destination_path} 301")

    return "\n".join(redirect_lines) + "\n"

NOT_FOUND_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Not Found | Shadowfetch</title>
  <meta name="description" content="The page you were looking for was not found.">
  <meta name="theme-color" content="#05070A">
  <link rel="stylesheet" href="/assets/styles.css?v=""" + ASSET_VERSION + """">
</head>
<body data-edition="studio" data-page="not-found">
  <main class="container" style="padding: 5rem 0; text-align: center;">
    <p style="font-size: 0.8rem; letter-spacing: 0.16em; text-transform: uppercase; color: #8fb0ff; margin: 0 0 1rem;">Shadowfetch</p>
    <h1 style="font-family: 'Playfair Display', Georgia, serif; font-size: 2.8rem; margin: 0 0 1rem;">This page was not found.</h1>
    <p style="font-size: 1.05rem; color: #a7b3c8; margin: 0 0 2rem;">Return to the primary site and continue from the current Shadowfetch architecture.</p>
    <a href="/" style="display: inline-flex; align-items: center; justify-content: center; min-height: 3rem; padding: 0.85rem 1.5rem; border-radius: 999px; background: linear-gradient(135deg, #3d6cff, #2e5bff 58%, #1b3fbe); color: #ffffff; font-size: 0.9rem; font-weight: 600; text-decoration: none;">Return Home</a>
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
    (DIST / "_redirects").write_text(build_redirects_content(), encoding="utf-8")
    (DIST / "404.html").write_text(NOT_FOUND_HTML, encoding="utf-8")


if __name__ == "__main__":
    main()
