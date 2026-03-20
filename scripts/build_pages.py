#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "assets" / "data" / "feed-config.json"
SECTION_ROOT = ROOT / "sections"
CNAME_PATH = ROOT / "CNAME"
SITEMAP_PATH = ROOT / "sitemap.xml"
ROBOTS_PATH = ROOT / "robots.txt"


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    build_section_pages(config)
    build_sitemap(config)
    build_robots()


def build_section_pages(config: dict) -> None:
    SECTION_ROOT.mkdir(parents=True, exist_ok=True)

    for section in config.get("sections", []):
        page_dir = SECTION_ROOT / section["key"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(section_page_markup(section), encoding="utf-8")


def build_sitemap(config: dict) -> None:
    base_url = f"https://{CNAME_PATH.read_text(encoding='utf-8').strip()}"
    now = datetime.now(timezone.utc).date().isoformat()
    routes = [
        "/",
        "/latest/",
        "/sections/",
        "/about/",
        *[f"/sections/{section['key']}/" for section in config.get("sections", [])],
    ]

    entries = "\n".join(
        f"""  <url>
    <loc>{base_url}{route}</loc>
    <lastmod>{now}</lastmod>
  </url>"""
        for route in routes
    )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""
    SITEMAP_PATH.write_text(sitemap, encoding="utf-8")


def build_robots() -> None:
    base_url = f"https://{CNAME_PATH.read_text(encoding='utf-8').strip()}"
    robots = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    ROBOTS_PATH.write_text(robots, encoding="utf-8")


def section_page_markup(section: dict) -> str:
    title = escape(section["title"])
    description = escape(section.get("description", ""))
    key = escape(section["key"])
    canonical_url = f"https://{CNAME_PATH.read_text(encoding='utf-8').strip()}/sections/{key}/"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | ShadowFetch News</title>
  <meta
    name="description"
    content="{title} on ShadowFetch News. {description}"
  >
  <meta name="theme-color" content="#071019">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{title} | ShadowFetch News">
  <meta
    property="og:description"
    content="{title} on ShadowFetch News. {description}"
  >
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="ShadowFetch News">
  <meta property="og:url" content="{canonical_url}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title} | ShadowFetch News">
  <meta
    name="twitter:description"
    content="{title} on ShadowFetch News. {description}"
  >
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;700&display=swap"
    rel="stylesheet"
  >
  <link rel="icon" href="/assets/shadowfetch-mark.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/styles.css">
</head>
<body data-page="section" data-section-key="{key}">
  <div class="page-orb orb-left" aria-hidden="true"></div>
  <div class="page-orb orb-right" aria-hidden="true"></div>

  <header class="site-chrome">
    <div class="utility-bar">
      <div class="container utility-wrap">
        <div class="utility-pill">
          <span class="utility-label">Visitor Counter</span>
          <strong data-visit-count>Loading...</strong>
        </div>
        <div class="utility-pill utility-status">
          <span class="utility-label">Snapshot</span>
          <strong data-generated-at>Waiting for feed data...</strong>
        </div>
        <div class="utility-links">
          <a class="utility-link" data-social-link="x" href="#" target="_blank" rel="noreferrer noopener">X / Twitter</a>
          <a class="utility-link" data-social-link="bluesky" href="#" target="_blank" rel="noreferrer noopener">Bluesky</a>
        </div>
      </div>
    </div>

    <div class="masthead">
      <div class="container masthead-wrap">
        <a class="brand" href="/" aria-label="ShadowFetch News home">
          <img src="/assets/shadowfetch-mark.svg" alt="" width="42" height="42">
          <span>
            <strong>ShadowFetch News</strong>
            <small>Late-breaking headlines across every beat</small>
          </span>
        </a>

        <nav class="site-nav" aria-label="Primary">
          <a href="/">Front Page</a>
          <a href="/latest/">Late Breaking</a>
          <a href="/sections/" aria-current="page">Sections</a>
          <a href="/about/">About</a>
        </nav>
      </div>
    </div>

    <div class="ticker-bar">
      <div class="container ticker-wrap">
        <span class="ticker-label">Late Breaking</span>
        <div class="ticker-window" aria-live="polite">
          <div class="ticker-track" id="breaking-ticker-track">
            <span class="ticker-placeholder">Loading breaking headlines...</span>
          </div>
        </div>
      </div>
    </div>
  </header>

  <main>
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Section Desk</p>
        <h1 id="section-detail-title">{title}</h1>
        <p class="hero-text" id="section-detail-description">{description}</p>
        <p class="toolbar-summary" id="section-detail-summary">Preparing this desk...</p>

        <div class="section-kpi-grid">
          <article class="section-kpi">
            <span class="stat-label">Sources</span>
            <strong id="section-source-count">--</strong>
          </article>
          <article class="section-kpi">
            <span class="stat-label">Stories</span>
            <strong id="section-story-count">--</strong>
          </article>
        </div>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-detail-shell">
        <div id="section-lead-story">
          <p class="loading-card">Loading the section lead...</p>
        </div>

        <aside class="panel section-sidebar">
          <p class="panel-label">Source Wall</p>
          <h2>Feeds powering this desk</h2>
          <p>The source mix below is specific to this section so readers can quickly understand where the briefing comes from.</p>
          <div class="source-row" id="section-source-row">
            <p class="loading-card">Loading sources...</p>
          </div>
        </aside>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">More From This Desk</p>
          <h2>Recent stories in {title}</h2>
        </div>
        <p class="section-copy">
          This page is meant to be the cleanest way to follow a single beat without getting lost in the broader front page mix.
        </p>
      </div>

      <div class="section-detail-grid" id="section-story-grid">
        <p class="loading-card">Loading section stories...</p>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-wrap">
      <div>
        <p class="footer-title">ShadowFetch News</p>
        <p class="footer-copy">A multi-page static newsroom with dedicated section desks and prepared feed snapshots.</p>
      </div>
      <div class="footer-links">
        <a href="/">Front Page</a>
        <a href="/latest/">Late Breaking</a>
        <a href="/sections/">Sections</a>
      </div>
    </div>
  </footer>

  <script src="/assets/app.js"></script>
</body>
</html>
"""


def escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
