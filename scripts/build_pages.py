#!/usr/bin/env python3

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "templates"

CONFIG_PATH = ROOT / "assets" / "data" / "feed-config.json"
FEED_DATA_PATH = ROOT / "assets" / "data" / "feed.json"

INDEX_TEMPLATE_PATH = TEMPLATE_ROOT / "index.html"
LATEST_TEMPLATE_PATH = TEMPLATE_ROOT / "latest.html"
SECTIONS_TEMPLATE_PATH = TEMPLATE_ROOT / "sections.html"
ABOUT_TEMPLATE_PATH = TEMPLATE_ROOT / "about.html"

INDEX_PATH = ROOT / "index.html"
LATEST_PATH = ROOT / "latest" / "index.html"
SECTIONS_INDEX_PATH = ROOT / "sections" / "index.html"
ABOUT_PATH = ROOT / "about" / "index.html"

SECTION_ROOT = ROOT / "sections"
CNAME_PATH = ROOT / "CNAME"
SITEMAP_PATH = ROOT / "sitemap.xml"
ROBOTS_PATH = ROOT / "robots.txt"

COUNTER_URL = "https://api.counterapi.dev/v1/shadowfetch-news/site-visits/"
SOCIAL_X_URL = "https://x.com/MrBobCorbin"
SOCIAL_BLUESKY_URL = "https://bsky.app/profile/mrbobcorbin.bsky.social"
SOCIAL_KALSHI_URL = "https://kalshi.com/sign-up/?referral=6ca54e6d-a516-4918-bc0a-829b18f99f70"


def main() -> None:
    config = load_json(CONFIG_PATH)
    payload = normalize_payload(load_json(FEED_DATA_PATH))
    context = build_site_context(config, payload)

    build_primary_pages(config, payload, context)
    build_section_pages(config, payload, context)
    build_sitemap(config)
    build_robots()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_payload(payload: dict) -> dict:
    payload = dict(payload)
    payload["latest"] = sorted(payload.get("latest", []), key=story_sort_key, reverse=True)
    payload["featured"] = payload.get("featured") or payload["latest"][:3]
    payload["sections"] = [
        {
            **section,
            "stories": sorted(section.get("stories", []), key=story_sort_key, reverse=True),
        }
        for section in payload.get("sections", [])
    ]
    return payload


def build_site_context(config: dict, payload: dict) -> dict:
    source_count = sum(len(section.get("sources", [])) for section in config.get("sections", []))
    visit_count = format_integer(fetch_counter_value())
    generated_at = f"{format_story_time(payload.get('generated_at'))} • Prepared snapshot"

    return {
        "section_count": str(len(config.get("sections", []))),
        "source_count": str(source_count),
        "visit_count": visit_count,
        "generated_at": escape(generated_at),
        "breaking_ticker": render_breaking_ticker(payload.get("latest", []), config.get("breaking_limit", 12)),
        "source_summary": escape(
            f"The site currently tracks {len(config.get('sections', []))} sections across {source_count} feed sources, "
            "mixing official institutional feeds with long-running publisher feeds."
        ),
    }


def fetch_counter_value() -> int:
    req = request.Request(
        COUNTER_URL,
        headers={"User-Agent": "ShadowFetchNewsBot/1.0 (+https://shadowfetch.com)"},
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return int(payload.get("count", payload.get("value", 0)))
    except error.HTTPError as exc:
        if exc.code in {400, 404}:
            return 0
        return 0
    except Exception:
        return 0


def build_primary_pages(config: dict, payload: dict, context: dict) -> None:
    latest_limit = config.get("latest_page_limit", 36)
    home_latest_limit = config.get("home_latest_limit", 12)
    home_section_story_limit = config.get("home_section_story_limit", 3)

    section_lookup = {section["key"]: section for section in payload.get("sections", [])}

    render_template_to(
        INDEX_TEMPLATE_PATH,
        INDEX_PATH,
        {
            "VISITOR_COUNT": context["visit_count"],
            "GENERATED_AT": context["generated_at"],
            "BREAKING_TICKER": context["breaking_ticker"],
            "SECTION_COUNT": context["section_count"],
            "SOURCE_COUNT": context["source_count"],
            "FEATURED_GRID": render_featured_grid(payload.get("featured", [])),
            "HOME_SECTION_GRID": render_home_section_grid(
                config.get("sections", []),
                section_lookup,
                home_section_story_limit,
            ),
            "HOME_FILTER_TOOLBAR": render_filter_links(config.get("sections", []), "/latest/"),
            "HOME_LATEST_SUMMARY": escape(render_story_summary(payload.get("latest", []), home_latest_limit)),
            "HOME_LATEST_GRID": render_story_grid(payload.get("latest", [])[:home_latest_limit]),
        },
    )

    render_template_to(
        LATEST_TEMPLATE_PATH,
        LATEST_PATH,
        {
            "VISITOR_COUNT": context["visit_count"],
            "GENERATED_AT": context["generated_at"],
            "BREAKING_TICKER": context["breaking_ticker"],
            "ARCHIVE_FILTER_TOOLBAR": render_filter_links(config.get("sections", []), "/latest/"),
            "ARCHIVE_SUMMARY": escape(render_story_summary(payload.get("latest", []), latest_limit)),
            "ARCHIVE_GRID": render_story_grid(payload.get("latest", [])[:latest_limit]),
        },
    )

    render_template_to(
        SECTIONS_TEMPLATE_PATH,
        SECTIONS_INDEX_PATH,
        {
            "VISITOR_COUNT": context["visit_count"],
            "GENERATED_AT": context["generated_at"],
            "BREAKING_TICKER": context["breaking_ticker"],
            "SECTION_DIRECTORY": render_section_directory(config.get("sections", []), section_lookup),
        },
    )

    render_template_to(
        ABOUT_TEMPLATE_PATH,
        ABOUT_PATH,
        {
            "VISITOR_COUNT": context["visit_count"],
            "GENERATED_AT": context["generated_at"],
            "BREAKING_TICKER": context["breaking_ticker"],
            "SOURCE_SUMMARY": context["source_summary"],
            "SOURCE_WALL": render_source_wall(config.get("sections", [])),
        },
    )


def render_template_to(template_path: Path, output_path: Path, mapping: dict[str, str]) -> None:
    html = template_path.read_text(encoding="utf-8")
    for key, value in mapping.items():
        html = html.replace(f"__{key}__", value)
    output_path.write_text(html, encoding="utf-8")


def build_section_pages(config: dict, payload: dict, context: dict) -> None:
    SECTION_ROOT.mkdir(parents=True, exist_ok=True)
    section_lookup = {section["key"]: section for section in payload.get("sections", [])}

    for section_config in config.get("sections", []):
        page_dir = SECTION_ROOT / section_config["key"]
        page_dir.mkdir(parents=True, exist_ok=True)
        section_payload = section_lookup.get(
            section_config["key"],
            {
                "stories": [],
                "successful_sources": 0,
                "total_sources": len(section_config.get("sources", [])),
            },
        )
        (page_dir / "index.html").write_text(
            section_page_markup(section_config, section_payload, context),
            encoding="utf-8",
        )


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


def section_page_markup(section_config: dict, section_payload: dict, context: dict) -> str:
    title = escape(section_config["title"])
    description = escape(section_config.get("description", ""))
    key = escape(section_config["key"])
    canonical_url = f"https://{CNAME_PATH.read_text(encoding='utf-8').strip()}/sections/{key}/"
    stories = section_payload.get("stories", [])
    lead_story = stories[0] if stories else None
    other_stories = stories[1:]
    source_count = len(section_config.get("sources", []))
    story_count = len(stories)
    summary = escape(
        f"This desk currently tracks {story_count} prepared {'story' if story_count == 1 else 'stories'} "
        f"from {section_payload.get('successful_sources', 0)}/{section_payload.get('total_sources', 0)} active sources."
    )

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
          <strong data-visit-count>{context['visit_count']}</strong>
        </div>
        <div class="utility-pill utility-status">
          <span class="utility-label">Snapshot</span>
          <strong data-generated-at>{context['generated_at']}</strong>
        </div>
        <div class="utility-links">
          <a class="utility-link" data-social-link="x" href="{SOCIAL_X_URL}" target="_blank" rel="noreferrer noopener">X / Twitter</a>
          <a class="utility-link" data-social-link="bluesky" href="{SOCIAL_BLUESKY_URL}" target="_blank" rel="noreferrer noopener">Bluesky</a>
          <a class="utility-link" data-social-link="kalshi" href="{SOCIAL_KALSHI_URL}" target="_blank" rel="noreferrer noopener">Kalshi</a>
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
            {context['breaking_ticker']}
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
        <p class="toolbar-summary" id="section-detail-summary">{summary}</p>

        <div class="section-kpi-grid">
          <article class="section-kpi">
            <span class="stat-label">Sources</span>
            <strong id="section-source-count">{source_count}</strong>
          </article>
          <article class="section-kpi">
            <span class="stat-label">Stories</span>
            <strong id="section-story-count">{story_count}</strong>
          </article>
        </div>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-detail-shell">
        <div id="section-lead-story">
          {render_section_lead(lead_story)}
        </div>

        <aside class="panel section-sidebar">
          <p class="panel-label">Source Wall</p>
          <h2>Feeds powering this desk</h2>
          <p>The source mix below is specific to this section so readers can quickly understand where the briefing comes from.</p>
          <div class="source-row" id="section-source-row">
            {render_source_row(section_config.get("sources", []))}
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
        {render_story_grid(other_stories, empty_message="More section stories will appear here when the feed refreshes.")}
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


def render_breaking_ticker(stories: list[dict], limit: int) -> str:
    if not stories:
        return '<span class="ticker-placeholder">Breaking headlines are temporarily unavailable.</span>'

    items = [
        f'<a class="ticker-item" href="{safe_url(story.get("link", ""))}" target="_blank" rel="noreferrer noopener"><span>{escape(story.get("title", "Untitled story"))}</span></a>'
        for story in stories[:limit]
    ]
    content = '\n<span class="ticker-divider" aria-hidden="true">•</span>\n'.join(items)
    return f"{content}{content}"


def render_featured_grid(stories: list[dict]) -> str:
    if not stories:
        return '<p class="empty-card">Featured stories are not available yet.</p>'

    lead = stories[0]
    side_markup = "".join(
        f"""
    <a class="featured-side" href="{safe_url(story.get('link', ''))}" target="_blank" rel="noreferrer noopener">
      {story_meta_markup(story)}
      <h3>{escape(story.get('title', 'Untitled story'))}</h3>
      <p>{escape(story.get('summary', 'Open the original source for the full story.'))}</p>
    </a>
"""
        for story in stories[1:3]
    )

    return f"""
    <a class="featured-main" href="{safe_url(lead.get('link', ''))}" target="_blank" rel="noreferrer noopener">
      {story_meta_markup(lead)}
      <h2>{escape(lead.get('title', 'Untitled story'))}</h2>
      <p>{escape(lead.get('summary', 'Open the original source for the full story.'))}</p>
      <span class="story-link">Read the full source</span>
    </a>
    <div class="featured-side-grid">
      {side_markup}
    </div>
"""


def render_home_section_grid(section_configs: list[dict], section_lookup: dict[str, dict], story_limit: int) -> str:
    cards = []
    for section_config in section_configs:
        section = section_lookup.get(section_config["key"], {"stories": []})
        stories = section.get("stories", [])[:story_limit]
        story_markup = (
            "".join(compact_story_markup(story) for story in stories)
            if stories
            else '<p class="empty-card">No stories available for this section right now.</p>'
        )
        cards.append(
            f"""
      <article class="section-card" id="section-{escape(section_config['key'])}">
        <p class="panel-label">{escape(section_config.get('short_label', section_config['title']))}</p>
        <h3>{escape(section_config['title'])}</h3>
        <p>{escape(section_config.get('description', ''))}</p>
        <div class="story-list">{story_markup}</div>
        <a class="story-link" href="/sections/{escape(section_config['key'])}/">Open section</a>
      </article>
"""
        )
    return "".join(cards)


def render_filter_links(section_configs: list[dict], all_href: str) -> str:
    links = [filter_link_markup("All Stories", all_href, True)]
    links.extend(
        filter_link_markup(
            section.get("short_label", section["title"]),
            f"/sections/{section['key']}/",
            False,
        )
        for section in section_configs
    )
    return "\n".join(links)


def filter_link_markup(label: str, href: str, pressed: bool) -> str:
    return (
        f'<a class="filter-pill" href="{safe_url_absolute_or_path(href)}" '
        f'aria-pressed="{"true" if pressed else "false"}">{escape(label)}</a>'
    )


def render_story_summary(stories: list[dict], limit: int) -> str:
    count = min(len(stories), limit)
    return f"Showing {count} {'story' if count == 1 else 'stories'} across every section in this view."


def render_story_grid(stories: list[dict], empty_message: str = "The story collection is temporarily empty.") -> str:
    if not stories:
        return f'<p class="empty-card">{escape(empty_message)}</p>'
    return "".join(story_card_markup(story) for story in stories)


def render_section_directory(section_configs: list[dict], section_lookup: dict[str, dict]) -> str:
    cards = []
    for section_config in section_configs:
        section = section_lookup.get(section_config["key"], {"stories": []})
        stories = section.get("stories", [])[:4]
        story_markup = (
            "".join(compact_story_markup(story) for story in stories)
            if stories
            else '<p class="empty-card">No stories available right now.</p>'
        )
        cards.append(
            f"""
      <article class="directory-card" id="section-{escape(section_config['key'])}">
        <p class="panel-label">{escape(section_config.get('short_label', section_config['title']))}</p>
        <h3>{escape(section_config['title'])}</h3>
        <p>{escape(section_config.get('description', ''))}</p>
        <div class="source-row">{render_source_row(section_config.get('sources', []))}</div>
        <div class="story-list">{story_markup}</div>
        <a class="story-link" href="/sections/{escape(section_config['key'])}/">Open {escape(section_config.get('short_label', section_config['title']))} desk</a>
      </article>
"""
        )
    return "".join(cards)


def render_source_row(sources: list[dict]) -> str:
    return "".join(
        f'<a class="source-chip" href="{safe_url(source.get("homepage") or source.get("url", ""))}" target="_blank" rel="noreferrer noopener">{escape(source.get("name", "Source"))}</a>'
        for source in sources
    )


def render_source_wall(section_configs: list[dict]) -> str:
    cards = []
    for section in section_configs:
        for source in section.get("sources", []):
            cards.append(
                f"""
        <a class="source-card" href="{safe_url(source.get('homepage') or source.get('url', ''))}" target="_blank" rel="noreferrer noopener">
          <span class="source-label">{escape(section['title'])}</span>
          <strong>{escape(source.get('name', 'Source'))}</strong>
        </a>
"""
            )
    return "".join(cards)


def render_section_lead(story: dict | None) -> str:
    if not story:
        return '<p class="empty-card">No lead story is available for this section right now.</p>'

    return f"""
      <a class="featured-main section-lead-card" href="{safe_url(story.get('link', ''))}" target="_blank" rel="noreferrer noopener">
        {story_meta_markup(story)}
        <h2>{escape(story.get('title', 'Untitled story'))}</h2>
        <p>{escape(story.get('summary', 'Open the original source for the full story.'))}</p>
        <span class="story-link">Read the full source</span>
      </a>
"""


def story_card_markup(story: dict) -> str:
    return f"""
    <a class="story-card" href="{safe_url(story.get('link', ''))}" target="_blank" rel="noreferrer noopener">
      {story_meta_markup(story)}
      <h3>{escape(story.get('title', 'Untitled story'))}</h3>
      <p>{escape(story.get('summary', 'Open the original source for the full story.'))}</p>
    </a>
"""


def compact_story_markup(story: dict) -> str:
    return f"""
    <a class="story-compact" href="{safe_url(story.get('link', ''))}" target="_blank" rel="noreferrer noopener">
      <div class="story-meta">
        <span class="story-source">{escape(story.get('source', 'Source'))}</span>
        <span class="story-time">{escape(format_story_time(story.get('timestamp')))}</span>
      </div>
      <h3>{escape(story.get('title', 'Untitled story'))}</h3>
      <p>{escape(story.get('summary', 'Open the original source for the full story.'))}</p>
    </a>
"""


def story_meta_markup(story: dict) -> str:
    return f"""
      <div class="story-meta">
        <span class="story-tag">{escape(story.get('section', 'General'))}</span>
        <span class="story-source">{escape(story.get('source', 'Source'))}</span>
        <span class="story-time">{escape(format_story_time(story.get('timestamp')))}</span>
      </div>
"""


def story_sort_key(story: dict) -> datetime:
    return parse_timestamp(story.get("timestamp"))


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def format_story_time(value: str | None) -> str:
    parsed = parse_timestamp(value)
    month = parsed.strftime("%b")
    day = str(parsed.day)
    hour = parsed.strftime("%I").lstrip("0") or "12"
    minute = parsed.strftime("%M")
    meridiem = parsed.strftime("%p")
    return f"{month} {day}, {hour}:{minute} {meridiem}"


def format_integer(value: int) -> str:
    return f"{value:,}"


def safe_url(url: str) -> str:
    try:
        parsed = parse.urlparse(url)
        return url if parsed.scheme in {"http", "https"} else "#"
    except Exception:
        return "#"


def safe_url_absolute_or_path(url: str) -> str:
    if url.startswith("/"):
        return url
    return safe_url(url)


def escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


if __name__ == "__main__":
    main()
