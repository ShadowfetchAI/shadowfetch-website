#!/usr/bin/env python3

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

DIRECTORIES = [
    "about",
    "archive",
    "assets",
    "briefs",
    "coverage",
    "journal",
    "latest",
    "roundups",
    "search",
    "sections",
    "sources",
    "topics",
]

FILES = [
    "feed.xml",
    "index.html",
    "robots.txt",
    "sitemap.xml",
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
  <title>Stop The Presses | ShadowFetch News</title>
  <meta name="description" content="The page you were looking for is not on this edition of ShadowFetch News.">
  <meta name="theme-color" content="#f2ebde">
  <link rel="stylesheet" href="/assets/styles.css">
</head>
<body data-page="not-found">
  <main class="container" style="padding: 5rem 0;">
    <section class="story-card" style="max-width: 48rem; margin: 0 auto; text-align: center;">
      <p class="eyebrow">Stop The Presses</p>
      <h1>This page missed the morning edition.</h1>
      <p>
        The link may be old, the story may have moved, or the page was never printed.
        Let’s get you back to the front page.
      </p>
      <div class="hero-actions" style="justify-content: center;">
        <a class="button button-primary" href="/">Return to the front page</a>
        <a class="button button-secondary" href="/search/">Search the newsroom</a>
      </div>
    </section>
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
