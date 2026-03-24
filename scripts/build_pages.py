#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = ROOT / "assets" / "data" / "feed-config.json"
FEED_DATA_PATH = ROOT / "assets" / "data" / "feed.json"
SEARCH_INDEX_PATH = ROOT / "assets" / "data" / "search-index.json"

INDEX_PATH = ROOT / "index.html"
LATEST_PATH = ROOT / "latest" / "index.html"
SECTIONS_INDEX_PATH = ROOT / "sections" / "index.html"
ABOUT_PATH = ROOT / "about" / "index.html"
TOPICS_INDEX_PATH = ROOT / "topics" / "index.html"
SEARCH_PATH = ROOT / "search" / "index.html"
ARCHIVE_INDEX_PATH = ROOT / "archive" / "index.html"
SOURCES_INDEX_PATH = ROOT / "sources" / "index.html"
ROUNDUP_TODAY_PATH = ROOT / "roundups" / "today" / "index.html"
RSS_FEED_PATH = ROOT / "feed.xml"
OG_DEFAULT_IMAGE = "https://shadowfetch.com/assets/shadowfetch-og.png"

SECTION_ROOT = ROOT / "sections"
TOPIC_ROOT = ROOT / "topics"
SOURCE_ROOT = ROOT / "sources"
BRIEF_ROOT = ROOT / "briefs"
COVERAGE_ROOT = ROOT / "coverage"
ARCHIVE_ROOT = ROOT / "archive"
ROUNDUP_ROOT = ROOT / "roundups"

CNAME_PATH = ROOT / "CNAME"
SITEMAP_PATH = ROOT / "sitemap.xml"
ROBOTS_PATH = ROOT / "robots.txt"

COUNTER_URL = "https://api.counterapi.dev/v1/shadowfetch-news/site-visits/"
SOCIAL_X_URL = "https://x.com/MrBobCorbin"
SOCIAL_BLUESKY_URL = "https://bsky.app/profile/mrbobcorbin.bsky.social"
SOCIAL_KALSHI_URL = "https://kalshi.com/sign-up/?referral=6ca54e6d-a516-4918-bc0a-829b18f99f70"

STOPWORDS = {
    "about",
    "after",
    "also",
    "amid",
    "around",
    "because",
    "being",
    "between",
    "could",
    "drive",
    "from",
    "have",
    "into",
    "just",
    "more",
    "over",
    "says",
    "than",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "under",
    "when",
    "with",
    "would",
    "your",
}

SECTION_CONTEXT = {
    "top-stories": "It is shaping the broader news cycle, which usually means readers will keep seeing follow-on reporting and political reaction around it.",
    "world": "It carries international consequences and is likely to keep generating diplomatic, economic, or security fallout beyond the first headline.",
    "business-markets": "It has a direct line into rates, prices, corporate behavior, or market sentiment, which makes it one of the day’s practical stories to watch.",
    "technology": "It sits inside a larger shift in platforms, software, or digital infrastructure, which is why this beat tends to move from niche to mainstream quickly.",
    "science-space": "It signals a broader science or exploration trend rather than a one-off curiosity, making it worth following after the first update lands.",
    "climate-environment": "It connects environmental change to policy, infrastructure, or everyday life, which is why this beat keeps spilling into other sections.",
    "security-privacy": "It affects risk, trust, or digital safety, and those stories often matter well beyond the immediate technical audience.",
    "health": "It touches public health, treatment, or research in a way readers may need explained rather than simply linked past.",
    "sports": "It has enough momentum or cultural spillover to rise above routine scorekeeping and become part of the larger conversation.",
    "entertainment": "It is moving conversation in culture, media, or entertainment fast enough to deserve a more deliberate read than a quick headline glance.",
    "u-s-politics": "It influences power, public institutions, or the governing story of the day, so follow-up coverage is likely to build quickly.",
    "ai-machine-learning": "It sits at the intersection of research, product, and capital in ways that tend to ripple quickly into hiring, regulation, and the way people work.",
    "crypto-finance": "It touches digital assets, financial infrastructure, or regulatory posture in ways that move fast and often create second-order effects across markets.",
}


def main() -> None:
    config = load_json(CONFIG_PATH)
    payload = normalize_payload(load_json(FEED_DATA_PATH))
    model = build_site_model(config, payload)
    context = build_site_context(config, payload, model)

    build_primary_pages(config, model, context)
    build_section_pages(model, context)
    build_topic_pages(model, context)
    build_source_pages(model, context)
    build_brief_pages(model, context)
    build_coverage_pages(model, context)
    build_archive_pages(model, context)
    build_roundup_page(model, context)
    build_search_index(config, model)
    build_sitemap(model)
    build_robots()
    build_rss_feed(model)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_payload(payload: dict) -> dict:
    payload = dict(payload)
    payload["latest"] = sorted(payload.get("latest", []), key=story_sort_key, reverse=True)
    payload["featured"] = payload.get("featured") or payload["latest"][:4]
    payload["sections"] = [
        {
            **section,
            "stories": sorted(section.get("stories", []), key=story_sort_key, reverse=True),
        }
        for section in payload.get("sections", [])
    ]
    return payload


def build_site_model(config: dict, payload: dict) -> dict:
    base_url = site_base_url()
    section_configs = config.get("sections", [])
    section_config_lookup = {section["key"]: section for section in section_configs}
    section_payload_lookup = {section["key"]: section for section in payload.get("sections", [])}
    source_lookup = build_source_lookup(section_configs)

    story_cache: dict[str, dict] = {}

    def cached_story(raw_story: dict) -> dict:
        identity = story_identity(raw_story)
        existing = story_cache.get(identity)
        if existing:
            return existing

        annotated = annotate_story(raw_story, source_lookup)
        story_cache[identity] = annotated
        return annotated

    latest = [cached_story(story) for story in payload.get("latest", [])]
    featured = [cached_story(story) for story in payload.get("featured", [])]

    sections = []
    for section_config in section_configs:
        payload_section = section_payload_lookup.get(
            section_config["key"],
            {
                "stories": [],
                "successful_sources": 0,
                "total_sources": len(section_config.get("sources", [])),
            },
        )
        section_stories = [cached_story(story) for story in payload_section.get("stories", [])]
        sections.append(
            {
                "key": section_config["key"],
                "title": section_config["title"],
                "short_label": section_config.get("short_label", section_config["title"]),
                "description": section_config.get("description", ""),
                "path": f"/sections/{section_config['key']}/",
                "sources": section_config.get("sources", []),
                "stories": section_stories,
                "lead_story": section_stories[0] if section_stories else None,
                "successful_sources": payload_section.get("successful_sources", 0),
                "total_sources": payload_section.get("total_sources", len(section_config.get("sources", []))),
            }
        )

    stories = sorted(story_cache.values(), key=story_sort_key, reverse=True)

    topics = build_topic_records(config.get("topics", []), stories, config.get("topic_story_limit", 12))
    topic_lookup = {topic["key"]: topic for topic in topics}
    add_topic_refs_to_stories(stories, topics)

    coverage = build_coverage_clusters(latest, config.get("developing_limit", 6))
    attach_coverage_refs(stories, coverage)

    sources = build_source_records(source_lookup, stories)
    source_index = {source["key"]: source for source in sources}
    for story in stories:
        story["source_profile"] = source_index.get(story["source_key"])

    archives = build_archive_days(stories)
    editors_picks = select_editor_picks(stories, config.get("editor_pick_limit", 4), topic_lookup)

    return {
        "base_url": base_url,
        "sections": sections,
        "sections_by_key": {section["key"]: section for section in sections},
        "stories": stories,
        "latest": latest,
        "featured": featured,
        "topics": topics,
        "topics_by_key": topic_lookup,
        "coverage": coverage,
        "sources": sources,
        "sources_by_key": source_index,
        "archive_days": archives,
        "editors_picks": editors_picks,
        "generated_at": payload.get("generated_at"),
        "section_count": len(section_configs),
        "source_count": len(sources),
        "successful_sources": payload.get("successful_sources", 0),
        "total_sources": payload.get("total_sources", 0),
    }


def build_source_lookup(section_configs: list[dict]) -> dict[str, dict]:
    records: dict[str, dict] = {}

    for section in section_configs:
        section_ref = {
            "key": section["key"],
            "title": section["title"],
            "short_label": section.get("short_label", section["title"]),
            "path": f"/sections/{section['key']}/",
        }
        for source in section.get("sources", []):
            key = slugify(source.get("name", "source"))
            record = records.setdefault(
                key,
                {
                    "key": key,
                    "name": source.get("name", "Source"),
                    "homepage": source.get("homepage", ""),
                    "feed_url": source.get("url", ""),
                    "path": f"/sources/{key}/",
                    "sections": [],
                    "stories": [],
                },
            )
            if not any(existing["key"] == section_ref["key"] for existing in record["sections"]):
                record["sections"].append(section_ref)

    return records


def build_topic_records(topic_configs: list[dict], stories: list[dict], story_limit: int) -> list[dict]:
    records = []

    for topic in topic_configs:
        matched = [story for story in stories if story_matches_topic(story, topic)]
        matched.sort(key=story_sort_key, reverse=True)
        records.append(
            {
                "key": topic["key"],
                "title": topic["title"],
                "description": topic.get("description", ""),
                "keywords": topic.get("keywords", []),
                "path": f"/topics/{topic['key']}/",
                "stories": matched[:story_limit],
                "story_count": len(matched),
                "lead_story": matched[0] if matched else None,
            }
        )

    records.sort(key=lambda topic: (topic["story_count"], topic["title"].lower()), reverse=True)
    return records


def add_topic_refs_to_stories(stories: list[dict], topics: list[dict]) -> None:
    for story in stories:
        story["topic_keys"] = []
        story["topics"] = []

    for topic in topics:
        matched_ids = {story["id"] for story in topic["stories"]}
        for story in stories:
            if story["id"] not in matched_ids:
                continue
            story["topic_keys"].append(topic["key"])
            story["topics"].append(
                {
                    "key": topic["key"],
                    "title": topic["title"],
                    "path": topic["path"],
                }
            )


def build_source_records(source_lookup: dict[str, dict], stories: list[dict]) -> list[dict]:
    for source in source_lookup.values():
        source["stories"] = []

    for story in stories:
        source = source_lookup.get(story["source_key"])
        if source is not None:
            source["stories"].append(story)

    records = []
    for source in source_lookup.values():
        source_stories = sorted(source["stories"], key=story_sort_key, reverse=True)
        records.append(
            {
                **source,
                "story_count": len(source_stories),
                "lead_story": source_stories[0] if source_stories else None,
                "stories": source_stories[:18],
            }
        )

    records.sort(key=lambda source: (source["story_count"], source["name"].lower()), reverse=True)
    return records


def build_archive_days(stories: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for story in stories:
        grouped[story["date_key"]].append(story)

    days = []
    for date_key in sorted(grouped.keys(), reverse=True):
        stories_for_day = sorted(grouped[date_key], key=story_sort_key, reverse=True)
        days.append(
            {
                "date_key": date_key,
                "title": format_archive_date(date_key),
                "path": f"/archive/{date_key}/",
                "stories": stories_for_day,
                "story_count": len(stories_for_day),
            }
        )

    return days


def build_coverage_clusters(stories: list[dict], limit: int) -> list[dict]:
    clusters: list[dict] = []

    for story in stories:
        tokens = significant_tokens(story.get("title", ""))
        if len(tokens) < 2:
            continue

        placed = None
        for cluster in clusters:
            common = tokens & cluster["token_set"]
            if len(common) >= 2:
                placed = cluster
                break

        if placed is None:
            clusters.append(
                {
                    "lead_story": story,
                    "stories": [story],
                    "token_set": set(tokens),
                    "topic_keys": set(story.get("topic_keys", [])),
                    "sections": {story.get("section_key", "")},
                    "sources": {story.get("source_key", "")},
                }
            )
            continue

        if story["id"] in {existing["id"] for existing in placed["stories"]}:
            continue

        placed["stories"].append(story)
        placed["token_set"].update(tokens)
        placed["topic_keys"].update(story.get("topic_keys", []))
        placed["sections"].add(story.get("section_key", ""))
        placed["sources"].add(story.get("source_key", ""))

    finalized = []
    for cluster in clusters:
        cluster_stories = sorted(cluster["stories"], key=story_sort_key, reverse=True)
        if len(cluster_stories) < 2:
            continue

        lead_story = cluster_stories[0]
        slug = f"{slugify(lead_story['title'])[:60]}-cluster-{lead_story['id'][:6]}"
        finalized.append(
            {
                "slug": slug,
                "path": f"/coverage/{slug}/",
                "title": lead_story["title"],
                "summary": lead_story["summary"],
                "lead_story": lead_story,
                "stories": cluster_stories,
                "story_count": len(cluster_stories),
                "source_count": len(cluster["sources"]),
                "section_count": len(cluster["sections"]),
                "topic_keys": list(cluster["topic_keys"]),
            }
        )

    finalized.sort(
        key=lambda cluster: (cluster["story_count"], story_sort_key(cluster["lead_story"])),
        reverse=True,
    )
    return finalized[:limit]


def attach_coverage_refs(stories: list[dict], coverage_clusters: list[dict]) -> None:
    story_refs = {story["id"]: story for story in stories}
    for story in stories:
        story["coverage_links"] = []

    for cluster in coverage_clusters:
        for story in cluster["stories"]:
            cached = story_refs.get(story["id"])
            if cached is None:
                continue
            cached["coverage_links"].append(
                {
                    "title": cluster["title"],
                    "path": cluster["path"],
                    "story_count": cluster["story_count"],
                }
            )


def select_editor_picks(stories: list[dict], limit: int, topics_by_key: dict[str, dict]) -> list[dict]:
    picks: list[dict] = []
    used_sections = set()

    def score(story: dict) -> tuple:
        return (
            len(story.get("topic_keys", [])),
            len(story.get("coverage_links", [])),
            story_sort_key(story),
        )

    for story in sorted(stories, key=score, reverse=True):
        if story.get("section_key") in used_sections and len(used_sections) < limit:
            continue
        used_sections.add(story.get("section_key"))
        picks.append(
            {
                **story,
                "why_it_matters": build_why_it_matters(story, topics_by_key),
            }
        )
        if len(picks) >= limit:
            break

    return picks


def annotate_story(story: dict, source_lookup: dict[str, dict]) -> dict:
    identity = story_identity(story)
    digest = hashlib.md5(identity.encode("utf-8")).hexdigest()[:8]
    title = story.get("title", "Untitled story")
    slug = f"{slugify(title)[:70] or 'story'}-{digest}"
    source_key = story.get("source_key") or slugify(story.get("source", "source"))
    source = source_lookup.get(
        source_key,
        {
            "key": source_key,
            "name": story.get("source", "Source"),
            "homepage": story.get("source_homepage", ""),
            "feed_url": story.get("source_feed", ""),
            "path": f"/sources/{source_key}/",
            "sections": [],
        },
    )
    parsed = parse_timestamp(story.get("timestamp"))
    date_key = parsed.date().isoformat()

    return {
        **story,
        "id": digest,
        "slug": slug,
        "brief_path": f"/briefs/{slug}/",
        "section_path": f"/sections/{story.get('section_key', '')}/",
        "source_key": source["key"],
        "source_path": source["path"],
        "source_homepage": source.get("homepage", story.get("source_homepage", "")),
        "source_feed": source.get("feed_url", story.get("source_feed", "")),
        "date_key": date_key,
        "date_path": f"/archive/{date_key}/",
        "display_time": format_story_time(story.get("timestamp")),
        "relative_time": format_relative_time(story.get("timestamp")),
        "recency_class": recency_class(story.get("timestamp")),
        "topic_keys": [],
        "topics": [],
        "coverage_links": [],
        "is_breaking": is_breaking_story(story.get("timestamp")),
        "is_new": is_new_story(story.get("timestamp")),
        "reading_time": estimate_reading_time(story.get("title", ""), story.get("summary", "")),
    }


def build_site_context(config: dict, payload: dict, model: dict) -> dict:
    return {
        "visit_count": format_integer(fetch_counter_value()),
        "generated_at": escape(format_story_time(payload.get("generated_at"))),
        "breaking_ticker": render_breaking_ticker(model.get("latest", []), config.get("breaking_limit", 18)),
        "section_count": str(model.get("section_count", 0)),
        "source_count": str(model.get("source_count", 0)),
        "topic_count": str(len(model.get("topics", []))),
        "story_count": str(len(model.get("stories", []))),
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


def build_primary_pages(config: dict, model: dict, context: dict) -> None:
    latest_limit = int(config.get("latest_page_limit", 96))
    home_latest_limit = int(config.get("home_latest_limit", 18))

    INDEX_PATH.write_text(
        render_home_page(config, model, context, home_latest_limit),
        encoding="utf-8",
    )
    LATEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(
        render_latest_page(config, model, context, latest_limit),
        encoding="utf-8",
    )
    SECTIONS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECTIONS_INDEX_PATH.write_text(
        render_sections_page(model, context),
        encoding="utf-8",
    )
    ABOUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ABOUT_PATH.write_text(
        render_about_page(model, context),
        encoding="utf-8",
    )
    TOPICS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOPICS_INDEX_PATH.write_text(
        render_topics_index_page(model, context),
        encoding="utf-8",
    )
    SEARCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEARCH_PATH.write_text(
        render_search_page(model, context),
        encoding="utf-8",
    )
    ARCHIVE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_INDEX_PATH.write_text(
        render_archive_index_page(model, context),
        encoding="utf-8",
    )
    SOURCES_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_INDEX_PATH.write_text(
        render_sources_index_page(model, context),
        encoding="utf-8",
    )


def build_section_pages(model: dict, context: dict) -> None:
    for section in model.get("sections", []):
        page_dir = SECTION_ROOT / section["key"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_section_page(section, model, context),
            encoding="utf-8",
        )


def build_topic_pages(model: dict, context: dict) -> None:
    for topic in model.get("topics", []):
        page_dir = TOPIC_ROOT / topic["key"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_topic_page(topic, model, context),
            encoding="utf-8",
        )


def build_source_pages(model: dict, context: dict) -> None:
    for source in model.get("sources", []):
        page_dir = SOURCE_ROOT / source["key"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_source_page(source, model, context),
            encoding="utf-8",
        )


def build_brief_pages(model: dict, context: dict) -> None:
    BRIEF_ROOT.mkdir(parents=True, exist_ok=True)

    for story in model.get("stories", []):
        page_dir = BRIEF_ROOT / story["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_brief_page(story, model, context),
            encoding="utf-8",
        )


def build_coverage_pages(model: dict, context: dict) -> None:
    COVERAGE_ROOT.mkdir(parents=True, exist_ok=True)

    for cluster in model.get("coverage", []):
        page_dir = COVERAGE_ROOT / cluster["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_coverage_page(cluster, model, context),
            encoding="utf-8",
        )


def build_archive_pages(model: dict, context: dict) -> None:
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

    for day in model.get("archive_days", []):
        page_dir = ARCHIVE_ROOT / day["date_key"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_archive_day_page(day, model, context),
            encoding="utf-8",
        )


def build_roundup_page(model: dict, context: dict) -> None:
    ROUNDUP_TODAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROUNDUP_TODAY_PATH.write_text(
        render_roundup_today_page(model, context),
        encoding="utf-8",
    )


def build_search_index(config: dict, model: dict) -> None:
    documents = []
    story_limit = int(config.get("search_story_limit", 180))

    for story in model.get("stories", [])[:story_limit]:
        documents.append(
            {
                "title": story["title"],
                "summary": story["summary"],
                "path": story["brief_path"],
                "type": "Brief",
                "section": story["section"],
                "source": story["source"],
                "timestamp": story["timestamp"],
                "keywords": " ".join(topic["title"] for topic in story.get("topics", [])),
            }
        )

    for topic in model.get("topics", []):
        documents.append(
            {
                "title": topic["title"],
                "summary": topic["description"],
                "path": topic["path"],
                "type": "Topic",
                "section": "Topics",
                "source": f"{topic['story_count']} tracked stories",
                "timestamp": topic["lead_story"]["timestamp"] if topic.get("lead_story") else model.get("generated_at"),
                "keywords": " ".join(topic.get("keywords", [])),
            }
        )

    for source in model.get("sources", []):
        documents.append(
            {
                "title": source["name"],
                "summary": source_summary_text(source),
                "path": source["path"],
                "type": "Source",
                "section": "Sources",
                "source": f"{source['story_count']} recent stories",
                "timestamp": source["lead_story"]["timestamp"] if source.get("lead_story") else model.get("generated_at"),
                "keywords": " ".join(section["title"] for section in source.get("sections", [])),
            }
        )

    for cluster in model.get("coverage", []):
        documents.append(
            {
                "title": cluster["title"],
                "summary": coverage_summary_text(cluster),
                "path": cluster["path"],
                "type": "Coverage",
                "section": "Developing",
                "source": f"{cluster['story_count']} related reports",
                "timestamp": cluster["lead_story"]["timestamp"],
                "keywords": cluster["title"],
            }
        )

    SEARCH_INDEX_PATH.write_text(json.dumps(documents, indent=2), encoding="utf-8")


def build_rss_feed(model: dict) -> None:
    """Generate a standard RSS 2.0 feed from the latest stories."""
    stories = model.get("stories", [])[:40]
    base_url = model.get("base_url", "https://shadowfetch.com")

    items = []
    for story in stories:
        title = story.get("title", "Untitled")
        link = f"{base_url}{story['brief_path']}"
        description = story.get("summary", "")
        pub_date = story.get("display_time", "")
        source = story.get("source", "")
        section = story.get("section", "News")

        items.append(f"""  <item>
    <title><![CDATA[{title}]]></title>
    <link>{link}</link>
    <description><![CDATA[{description}]]></description>
    <pubDate>{pub_date}</pubDate>
    <category>{section}</category>
    <author>{source}</author>
    <guid isPermaLink="true">{link}</guid>
  </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>ShadowFetch News</title>
  <link>{base_url}</link>
  <description>Late-breaking headlines across every beat — aggregated, organized, and brief-first.</description>
  <language>en-us</language>
  <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml"/>
  <image>
    <url>{OG_DEFAULT_IMAGE}</url>
    <title>ShadowFetch News</title>
    <link>{base_url}</link>
  </image>
{"".join(items)}
</channel>
</rss>"""

    RSS_FEED_PATH.write_text(rss, encoding="utf-8")


def build_sitemap(model: dict) -> None:
    base_url = site_base_url()
    routes = [
        "/",
        "/latest/",
        "/sections/",
        "/about/",
        "/topics/",
        "/search/",
        "/archive/",
        "/sources/",
        "/roundups/today/",
    ]
    routes.extend(section["path"] for section in model.get("sections", []))
    routes.extend(topic["path"] for topic in model.get("topics", []))
    routes.extend(source["path"] for source in model.get("sources", []))
    routes.extend(cluster["path"] for cluster in model.get("coverage", []))
    routes.extend(day["path"] for day in model.get("archive_days", []))
    routes.extend(story["brief_path"] for story in model.get("stories", []))

    now = datetime.now(timezone.utc).date().isoformat()
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
    base_url = site_base_url()
    robots = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    ROBOTS_PATH.write_text(robots, encoding="utf-8")


def render_home_page(config: dict, model: dict, context: dict, latest_limit: int) -> str:
    featured = model.get("featured", [])[:4]
    sections = model.get("sections", [])
    coverage = model.get("coverage", [])
    topics = model.get("topics", [])[:6]
    editors_picks = model.get("editors_picks", [])

    hero = f"""
    <section class="container hero hero-home">
      <div class="hero-copy">
        <p class="eyebrow">Late-breaking coverage across the stories driving the day.</p>
        <h1>One front page for the headlines shaping politics, markets, science, culture, and everything moving fast.</h1>
        <p class="hero-text">
          ShadowFetch News now reads more like a newsroom: live briefs, topic hubs, source profiles,
          deeper desks, a faster archive, and cleaner paths from a headline into the broader story.
        </p>
        <div class="hero-actions">
          <a class="button button-primary" href="/latest/">Open the live wire</a>
          <a class="button button-secondary" href="/topics/">Track the big stories</a>
        </div>
        {render_search_form("", "hero")}
        <div class="hero-stats">
          <article>
            <span class="stat-label">Sections</span>
            <strong>{context['section_count']}</strong>
          </article>
          <article>
            <span class="stat-label">Sources</span>
            <strong>{context['source_count']}</strong>
          </article>
          <article>
            <span class="stat-label">Topics</span>
            <strong>{context['topic_count']}</strong>
          </article>
          <article>
            <span class="stat-label">Briefs</span>
            <strong>{context['story_count']}</strong>
          </article>
        </div>
      </div>

      <aside class="panel hero-note">
        <p class="panel-label">Today At A Glance</p>
        <h2>ShadowFetch now has more ways to follow the same day.</h2>
        <p>
          Start with the front page, jump into topic hubs when a story keeps growing,
          open briefs for extra context, or move desk by desk when you want a cleaner read on one beat.
        </p>
        <div class="stack-links">
          <a class="social-panel-link" href="/roundups/today/">
            <span>Daily Roundup</span>
            <strong>Open today’s editor package</strong>
          </a>
          <a class="social-panel-link" href="/archive/">
            <span>Archive</span>
            <strong>Browse the day by timestamp</strong>
          </a>
          <a class="social-panel-link" href="/sources/">
            <span>Sources</span>
            <strong>See who powers the page</strong>
          </a>
        </div>
      </aside>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Front Page</p>
          <h2>The strongest read on the day</h2>
        </div>
        <p class="section-copy">
          A bigger hierarchy now separates the main lead, the next layer of consequential stories,
          and the fastest routes into briefs, sections, and topic coverage.
        </p>
      </div>
      {render_featured_grid(featured)}
    </section>

    <section class="container page-section">
      <div class="quicklink-grid">
        {render_quicklink_card("Late Breaking", "The densest live stream across every section.", "/latest/")}
        {render_quicklink_card("Topics", "Follow the bigger story lines instead of one-off headlines.", "/topics/")}
        {render_quicklink_card("Roundup", "Open the day’s editor-style package in one pass.", "/roundups/today/")}
        {render_quicklink_card("Archive", "Browse stories by date and time when you need the timeline.", "/archive/")}
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Developing</p>
          <h2>Story lines still moving</h2>
        </div>
        <p class="section-copy">
          These cards group related reports so the site can track a developing subject rather than repeat one headline shape over and over.
        </p>
      </div>
      {render_developing_grid(coverage, topics)}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Editor’s Picks</p>
          <h2>Briefs worth opening first</h2>
        </div>
        <p class="section-copy">
          Each pick adds a short frame for why the story matters beyond the first headline.
        </p>
      </div>
      {render_editors_pick_grid(editors_picks)}
    </section>

    <section class="container page-section topic-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Topic Radar</p>
          <h2>Ongoing themes across the site</h2>
        </div>
        <p class="section-copy">
          Topic pages turn broad coverage into a more organized reading experience when one subject starts showing up everywhere.
        </p>
      </div>
      {render_topic_grid(topics)}
    </section>

    <section class="container page-section">
      <div class="social-shell">
        <article class="panel follow-card">
          <p class="panel-label">Follow Along</p>
          <h2>Keep ShadowFetch in your orbit.</h2>
          <p>Readers can find your accounts without hunting for them, and the links now sit in the header and in a dedicated promo block.</p>
          <div class="stack-links">
            <a class="social-panel-link" href="{SOCIAL_X_URL}" target="_blank" rel="noreferrer noopener">
              <span>X / Twitter</span>
              <strong>@MrBobCorbin</strong>
            </a>
            <a class="social-panel-link" href="{SOCIAL_BLUESKY_URL}" target="_blank" rel="noreferrer noopener">
              <span>Bluesky</span>
              <strong>mrbobcorbin.bsky.social</strong>
            </a>
            <a class="social-panel-link" href="{SOCIAL_KALSHI_URL}" target="_blank" rel="noreferrer noopener">
              <span>Kalshi</span>
              <strong>Join through your referral link</strong>
            </a>
          </div>
        </article>

        <article class="panel tip-card">
          <p class="panel-label">Search & Source</p>
          <h2>Find the angle you need faster.</h2>
          <p>
            Search now reaches into briefs, topic pages, source pages, and developing coverage pages, which makes the site much easier to navigate once it grows.
          </p>
          <div class="button-row">
            <a class="button button-secondary" href="/search/">Open Search</a>
            <a class="button button-secondary" href="/sources/">Browse Sources</a>
          </div>
        </article>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Coverage Map</p>
          <h2>All the desks in one pass</h2>
        </div>
        <p class="section-copy">
          Section pages now feed the larger newsroom shell, so each desk has a lead, its own source wall, and a cleaner stack of briefs.
        </p>
      </div>
      {render_section_overview_grid(sections, 3)}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Late Breaking</p>
          <h2>The live wire</h2>
        </div>
        <p class="section-copy">
          Use the filter buttons to narrow the stream by beat while keeping the same page fast and readable.
        </p>
      </div>
      {render_filter_toolbar(sections, "home-filter-toolbar", "home-latest-grid", "home-latest-summary")}
      <p class="toolbar-summary" id="home-latest-summary">{escape(render_story_summary(model.get('latest', []), latest_limit))}</p>
      <div class="story-grid story-grid-latest" id="home-latest-grid">
        {render_story_grid(model.get("latest", [])[:latest_limit])}
      </div>
    </section>
    """

    return page_shell(
        title="ShadowFetch News | Late-Breaking Headlines Across Every Beat",
        description="A broadened ShadowFetch News front page with late-breaking coverage, briefs, topic pages, source profiles, archive pages, and a stronger newsroom-style hierarchy.",
        canonical_path="/",
        context=context,
        nav_current="home",
        page_key="home",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="A broader front page with briefs, topics, source pages, archives, and cleaner ways to follow the day.",
    )


def render_latest_page(config: dict, model: dict, context: dict, latest_limit: int) -> str:
    sections = model.get("sections", [])
    archive_days = model.get("archive_days", [])[:6]
    coverage = model.get("coverage", [])[:1]

    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Live Archive</p>
        <h1>The fast stream, with better ways to cut through it.</h1>
        <p class="hero-text">
          This page is still the highest-density headline view, but it now sits beside archive pages,
          source profiles, and search so repeat visitors can move around the site with less friction.
        </p>
        {render_search_form("", "inline")}
      </div>
    </section>
    """

    spotlight_markup = render_developing_grid(coverage, []) if coverage else ""
    archive_links = "".join(
        f'<a class="source-chip" href="{day["path"]}">{escape(day["title"])} <span class="chip-count">{day["story_count"]}</span></a>'
        for day in archive_days
    )

    main_markup = f"""
    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Archive Tools</p>
          <h2>Latest first, but easier to navigate.</h2>
        </div>
        <p class="section-copy">
          Open today’s developing story cluster, jump into the date archive, or filter the live grid without leaving the page.
        </p>
      </div>
      {spotlight_markup}
      <div class="source-row archive-chip-row">{archive_links}</div>
    </section>

    <section class="container page-section">
      {render_filter_toolbar(sections, "archive-filter-toolbar", "archive-grid", "archive-summary")}
      <p class="toolbar-summary" id="archive-summary">{escape(render_story_summary(model.get('latest', []), latest_limit))}</p>
      <div class="story-grid story-grid-archive" id="archive-grid">
        {render_story_grid(model.get("latest", [])[:latest_limit])}
      </div>
    </section>
    """

    return page_shell(
        title="Late Breaking | ShadowFetch News",
        description="The late-breaking archive from ShadowFetch News, now paired with search, archive navigation, briefs, and developing-story coverage.",
        canonical_path="/latest/",
        context=context,
        nav_current="latest",
        page_key="latest",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="The late-breaking page is built for fast repeat visits, cleaner filtering, and a quicker route into deeper coverage.",
    )


def render_sections_page(model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Sections</p>
        <h1>Every desk, its source mix, and the freshest briefs behind it.</h1>
        <p class="hero-text">
          The section directory now works more like a newsroom map: each desk has a lead story,
          a source mix, and a cleaner trail into the part of the news cycle readers care about most.
        </p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      {render_section_overview_grid(model.get("sections", []), 4)}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Related Layers</p>
          <h2>Topics and sources behind the desks</h2>
        </div>
        <p class="section-copy">
          Section pages are now supported by topic pages and source profiles, which makes it easier to follow either the beat or the outlet.
        </p>
      </div>
      <div class="dual-grid">
        <article class="panel">
          <p class="panel-label">Topics</p>
          <h2>Track the larger story lines</h2>
          <div class="story-list">
            {render_topic_grid(model.get("topics", [])[:4])}
          </div>
        </article>
        <article class="panel">
          <p class="panel-label">Sources</p>
          <h2>See who powers the front page</h2>
          <div class="source-directory source-directory-mini">
            {render_source_directory(model.get("sources", [])[:6], compact=True)}
          </div>
        </article>
      </div>
    </section>
    """

    return page_shell(
        title="Sections | ShadowFetch News",
        description="Browse every ShadowFetch News desk, plus the sources and topic layers behind the section map.",
        canonical_path="/sections/",
        context=context,
        nav_current="sections",
        page_key="sections",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Section desks, source walls, and topic links make the broader site much easier to scan.",
    )


def render_about_page(model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">About</p>
        <h1>A broad news front page built to help readers move from headline to context faster.</h1>
        <p class="hero-text">
          ShadowFetch News is now built around a fuller editorial shell: briefs for individual stories,
          topic pages for ongoing threads, source profiles, section desks, search, and a day archive.
        </p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="about-grid">
        <article class="panel about-card">
          <p class="panel-label">Mission</p>
          <h2>Make the day easier to read.</h2>
          <p>
            The site is designed to help readers move quickly without losing the bigger picture:
            broad sections, developing-story groupings, and briefs that add a little more context before the click out.
          </p>
        </article>

        <article class="panel about-card">
          <p class="panel-label">Editorial Shape</p>
          <h2>Aggregation, but more organized.</h2>
          <p>
            ShadowFetch now layers headline aggregation with story briefs, topic hubs, source profiles,
            editor’s picks, and a daily roundup so the experience feels more like a publication than a feed wall.
          </p>
        </article>

        <article class="panel about-card">
          <p class="panel-label">Follow</p>
          <h2>Find MrBobCorbin</h2>
          <div class="stack-links">
            <a class="social-panel-link" href="{SOCIAL_X_URL}" target="_blank" rel="noreferrer noopener">
              <span>X / Twitter</span>
              <strong>@MrBobCorbin</strong>
            </a>
            <a class="social-panel-link" href="{SOCIAL_BLUESKY_URL}" target="_blank" rel="noreferrer noopener">
              <span>Bluesky</span>
              <strong>mrbobcorbin.bsky.social</strong>
            </a>
            <a class="social-panel-link" href="{SOCIAL_KALSHI_URL}" target="_blank" rel="noreferrer noopener">
              <span>Kalshi</span>
              <strong>Use your referral link</strong>
            </a>
          </div>
        </article>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Source Wall</p>
          <h2>The outlets and institutions behind the site</h2>
        </div>
        <p class="section-copy">
          The source wall now links into dedicated source pages so readers can see each outlet’s recent footprint on the site.
        </p>
      </div>
      <div class="source-wall">
        {render_source_wall(model.get("sources", []))}
      </div>
    </section>
    """

    return page_shell(
        title="About | ShadowFetch News",
        description="About ShadowFetch News, including the broader newsroom structure, source model, and where to follow MrBobCorbin.",
        canonical_path="/about/",
        context=context,
        nav_current="about",
        page_key="about",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Built around broad coverage, clearer story paths, and a source mix meant to stay dependable over time.",
    )


def render_topics_index_page(model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Topics</p>
        <h1>Track the subjects that keep cutting across the whole site.</h1>
        <p class="hero-text">
          Topic pages are the fastest way to follow ongoing story lines instead of chasing a single headline at a time.
        </p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      {render_topic_grid(model.get("topics", []), large=True)}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Developing</p>
          <h2>Related coverage pages</h2>
        </div>
        <p class="section-copy">
          Coverage pages group related reports when the site sees multiple stories converging around the same event or thread.
        </p>
      </div>
      {render_developing_grid(model.get("coverage", []), [])}
    </section>
    """

    return page_shell(
        title="Topics | ShadowFetch News",
        description="Track ShadowFetch News by larger topic, from conflict and markets to health, technology, and science.",
        canonical_path="/topics/",
        context=context,
        nav_current="topics",
        page_key="topics",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Topic pages make it easier to keep reading when one subject starts showing up across multiple sections.",
    )


def render_search_page(model: dict, context: dict) -> str:
    suggestions = "".join(
        f'<a class="source-chip" href="/search/?q={parse.quote(topic["title"])}">{escape(topic["title"])}</a>'
        for topic in model.get("topics", [])[:6]
    )

    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Search</p>
        <h1>Search briefs, topics, sources, and developing coverage.</h1>
        <p class="hero-text">
          Search now gives the newsroom a much more useful discovery layer across briefs, topics, sources, and coverage pages.
        </p>
        {render_search_form("", "search")}
        <div class="source-row">{suggestions}</div>
      </div>
    </section>
    """

    main_markup = """
    <section class="container page-section">
      <div class="search-results-shell">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Results</p>
            <h2 data-search-title>Search the newsroom</h2>
          </div>
          <p class="section-copy" data-search-summary>Type a topic, person, company, place, or source to pull up matching pages.</p>
        </div>
        <div class="search-results" id="search-results"></div>
        <p class="empty-card" id="search-empty">Enter a search above to explore the site.</p>
      </div>
    </section>
    """

    return page_shell(
        title="Search | ShadowFetch News",
        description="Search ShadowFetch News across briefs, topics, sources, and developing coverage pages.",
        canonical_path="/search/",
        context=context,
        nav_current="search",
        page_key="search",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Search reaches the site’s briefs, source pages, topic pages, and developing coverage hubs.",
    )


def render_archive_index_page(model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Archive</p>
        <h1>Browse the briefing by date.</h1>
        <p class="hero-text">
          Date pages make the site easier to use as a timeline instead of only a front page.
        </p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      {render_archive_directory(model.get("archive_days", []))}
    </section>
    """

    return page_shell(
        title="Archive | ShadowFetch News",
        description="Browse ShadowFetch News by date and open the story briefs that shaped each day’s front page.",
        canonical_path="/archive/",
        context=context,
        nav_current="archive",
        page_key="archive",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Archive pages let repeat readers move back through the day without losing the cleaner site structure.",
    )


def render_sources_index_page(model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Sources</p>
        <h1>Every source powering the site, with its own page and recent story trail.</h1>
        <p class="hero-text">
          Source pages make the feed mix legible instead of hidden behind cards.
        </p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Source Directory</p>
          <h2>Outlets and institutions in the mix</h2>
        </div>
        <p class="section-copy">
          Each source page shows its recent footprint on the site, the desks it appears in, and a direct link back to the original outlet.
        </p>
      </div>
      <div class="source-directory">
        {render_source_directory(model.get("sources", []))}
      </div>
    </section>
    """

    return page_shell(
        title="Sources | ShadowFetch News",
        description="Browse the outlets and institutions behind ShadowFetch News, with source pages for each feed in the mix.",
        canonical_path="/sources/",
        context=context,
        nav_current="sources",
        page_key="sources",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Source pages make the site’s feed mix much easier to understand and trust.",
    )


def render_section_page(section: dict, model: dict, context: dict) -> str:
    related_topics = related_topics_for_stories(section.get("stories", []), model.get("topics_by_key", {}))
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Section Desk</p>
        <h1>{escape(section['title'])}</h1>
        <p class="hero-text">{escape(section.get('description', ''))}</p>
        <div class="section-kpi-grid">
          <article class="section-kpi">
            <span class="stat-label">Stories</span>
            <strong>{len(section.get('stories', []))}</strong>
          </article>
          <article class="section-kpi">
            <span class="stat-label">Sources</span>
            <strong>{len(section.get('sources', []))}</strong>
          </article>
          <article class="section-kpi">
            <span class="stat-label">Active Feeds</span>
            <strong>{section.get('successful_sources', 0)}/{section.get('total_sources', 0)}</strong>
          </article>
        </div>
      </div>
      <aside class="panel hero-note">
        <p class="panel-label">Related Topics</p>
        <h2>Where this desk overlaps the bigger picture</h2>
        {render_topic_chip_row(related_topics[:4]) if related_topics else '<p>This desk will show related topic links as more story lines overlap.</p>'}
      </aside>
    </section>
    """

    lead_story = section.get("lead_story")
    main_markup = f"""
    <section class="container page-section">
      <div class="section-detail-shell">
        {render_story_feature(lead_story, "Section Lead", "Open brief") if lead_story else '<p class="empty-card">No lead story is available right now.</p>'}
        <aside class="panel section-sidebar">
          <p class="panel-label">Source Wall</p>
          <h2>Feeds behind this desk</h2>
          <p>This row now opens dedicated source pages first, making the source mix easier to inspect.</p>
          <div class="source-row">
            {render_source_row_from_configs(section.get("sources", []))}
          </div>
        </aside>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Recent Briefs</p>
          <h2>More from {escape(section['title'])}</h2>
        </div>
        <p class="section-copy">
          Every story card on this desk now opens into a brief page before the source click-out.
        </p>
      </div>
      <div class="story-grid story-grid-archive">
        {render_story_grid(section.get("stories", [])[1:])}
      </div>
    </section>
    """

    return page_shell(
        title=f"{section['title']} | ShadowFetch News",
        description=f"{section['title']} on ShadowFetch News. {section.get('description', '')}",
        canonical_path=section["path"],
        context=context,
        nav_current="sections",
        page_key="section",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Dedicated desks make it easier to follow one beat without losing the shape of the wider front page.",
        body_attrs={"data-section-key": section["key"]},
    )


def render_topic_page(topic: dict, model: dict, context: dict) -> str:
    related_clusters = [
        cluster
        for cluster in model.get("coverage", [])
        if topic["key"] in cluster.get("topic_keys", [])
    ]
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Topic Desk</p>
        <h1>{escape(topic['title'])}</h1>
        <p class="hero-text">{escape(topic.get('description', ''))}</p>
        <div class="hero-stats">
          <article>
            <span class="stat-label">Tracked Stories</span>
            <strong>{topic['story_count']}</strong>
          </article>
          <article>
            <span class="stat-label">Lead Story</span>
            <strong>{escape(topic['lead_story']['section']) if topic.get('lead_story') else 'Waiting'}</strong>
          </article>
        </div>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      {render_story_feature(topic.get("lead_story"), "Lead Brief", "Open brief") if topic.get("lead_story") else '<p class="empty-card">No lead story is available for this topic right now.</p>'}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Developing Coverage</p>
          <h2>Where this topic is clustering</h2>
        </div>
      </div>
      {render_developing_grid(related_clusters[:3], []) if related_clusters else '<p class="empty-card">No related coverage clusters are available for this topic yet.</p>'}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Topic Briefs</p>
          <h2>Stories tagged to this subject</h2>
        </div>
      </div>
      <div class="story-grid story-grid-archive">
        {render_story_grid(topic.get("stories", []))}
      </div>
    </section>
    """

    return page_shell(
        title=f"{topic['title']} | ShadowFetch News",
        description=f"{topic['title']} on ShadowFetch News. {topic.get('description', '')}",
        canonical_path=topic["path"],
        context=context,
        nav_current="topics",
        page_key="topic",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Topic pages help the site follow ongoing themes instead of treating every story as a one-off.",
    )


def render_source_page(source: dict, model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Source Profile</p>
        <h1>{escape(source['name'])}</h1>
        <p class="hero-text">{escape(source_summary_text(source))}</p>
        <div class="source-row">
          {''.join(f'<a class="source-chip" href="{section["path"]}">{escape(section["title"])}</a>' for section in source.get("sections", []))}
        </div>
      </div>
      <aside class="panel hero-note">
        <p class="panel-label">Open Source</p>
        <h2>Visit the original outlet</h2>
        <p>Each source page now links directly back to the publisher while showing that source’s recent footprint on ShadowFetch.</p>
        <div class="button-row">
          <a class="button button-secondary" href="{safe_url(source.get('homepage', ''))}" target="_blank" rel="noreferrer noopener">Open homepage</a>
          <a class="button button-secondary" href="{safe_url(source.get('feed_url', ''))}" target="_blank" rel="noreferrer noopener">Open feed</a>
        </div>
      </aside>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Recent Footprint</p>
          <h2>{escape(source['name'])} on ShadowFetch</h2>
        </div>
        <p class="section-copy">
          Open the brief for a little more context or click straight out to the original source from each card.
        </p>
      </div>
      <div class="story-grid story-grid-archive">
        {render_story_grid(source.get("stories", []))}
      </div>
    </section>
    """

    return page_shell(
        title=f"{source['name']} | ShadowFetch News",
        description=source_summary_text(source),
        canonical_path=source["path"],
        context=context,
        nav_current="sources",
        page_key="source",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Source pages make the site’s mix of outlets and institutions much easier to inspect.",
    )


def render_brief_page(story: dict, model: dict, context: dict) -> str:
    section = model.get("sections_by_key", {}).get(story.get("section_key"))
    related = related_stories_for_brief(story, model)
    coverage_links = story.get("coverage_links", [])
    why_it_matters = build_why_it_matters(story, model.get("topics_by_key", {}))

    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Story Brief</p>
        <h1>{escape(story['title'])}</h1>
        <div class="story-meta story-meta-large">
          <a class="story-tag" href="{story['section_path']}">{escape(story['section'])}</a>
          <a class="story-source" href="{story['source_path']}">{escape(story['source'])}</a>
          <span class="story-time">{escape(story['display_time'])}</span>
          <span class="story-recency {escape(story['recency_class'])}">{escape(story['relative_time'])}</span>
        </div>
        <p class="hero-text">{escape(story['summary'])}</p>
        <div class="button-row">
          <a class="button button-primary" href="{story['link']}" target="_blank" rel="noreferrer noopener">Open original source</a>
          <a class="button button-secondary" href="{story['section_path']}">Back to {escape(story['section'])}</a>
        </div>
        <div class="share-row">
          <span class="share-label">Share:</span>
          <a class="share-btn share-x" href="https://x.com/intent/tweet?text={parse.quote(story['title'])}&url=https://shadowfetch.com{story['brief_path']}" target="_blank" rel="noreferrer noopener">X / Twitter</a>
          <a class="share-btn share-bluesky" href="https://bsky.app/intent/compose?text={parse.quote(story['title'] + ' https://shadowfetch.com' + story['brief_path'])}" target="_blank" rel="noreferrer noopener">Bluesky</a>
        </div>
        <p class="story-reading-time-brief">{story.get('reading_time', '')}</p>
      </div>
    </section>
    """

    coverage_markup = (
        "".join(
            f'<a class="source-chip" href="{coverage["path"]}">{escape(coverage["title"])} <span class="chip-count">{coverage["story_count"]}</span></a>'
            for coverage in coverage_links
        )
        if coverage_links
        else "<p>This story is not part of a broader cluster yet.</p>"
    )

    topics_markup = render_topic_chip_row(story.get("topics", [])) if story.get("topics") else "<p>No topic tags are attached to this brief yet.</p>"
    section_description = escape(section.get("description", "")) if section else ""

    main_markup = f"""
    <section class="container page-section">
      <div class="brief-layout">
        <article class="panel brief-panel">
          <p class="panel-label">Why It Matters</p>
          <h2>A quick frame before the click out</h2>
          <p>{escape(why_it_matters)}</p>
          <p class="brief-note">{section_description}</p>
        </article>

        <article class="panel brief-panel">
          <p class="panel-label">Connected Coverage</p>
          <h2>More ways to keep reading</h2>
          <div class="stack-links">
            <a class="social-panel-link" href="{story['source_path']}">
              <span>Source Profile</span>
              <strong>{escape(story['source'])}</strong>
            </a>
            <a class="social-panel-link" href="{story['date_path']}">
              <span>Archive Day</span>
              <strong>{escape(format_archive_date(story['date_key']))}</strong>
            </a>
            <a class="social-panel-link" href="/search/?q={parse.quote(story['title'])}">
              <span>Search</span>
              <strong>Find related pages</strong>
            </a>
          </div>
        </article>
      </div>
    </section>

    <section class="container page-section">
      <div class="dual-grid">
        <article class="panel">
          <p class="panel-label">Topics</p>
          <h2>Where this brief fits</h2>
          {topics_markup}
        </article>
        <article class="panel">
          <p class="panel-label">Coverage Links</p>
          <h2>Related clusters</h2>
          {coverage_markup}
        </article>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Keep Reading</p>
          <h2>Related briefs and nearby stories</h2>
        </div>
        <p class="section-copy">
          ShadowFetch briefs are meant to keep readers inside the site just long enough to orient themselves before jumping out to a source.
        </p>
      </div>
      <div class="story-grid story-grid-archive">
        {render_story_grid(related)}
      </div>
    </section>
    """

    return page_shell(
        title=f"{story['title']} | ShadowFetch Brief",
        description=story["summary"],
        canonical_path=story["brief_path"],
        context=context,
        nav_current="",
        page_key="brief",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Brief pages add one more layer of context before the click out to the original source.",
    )


def render_coverage_page(cluster: dict, model: dict, context: dict) -> str:
    related_topics = [
        model.get("topics_by_key", {}).get(topic_key)
        for topic_key in cluster.get("topic_keys", [])
        if model.get("topics_by_key", {}).get(topic_key)
    ]

    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Developing Coverage</p>
        <h1>{escape(cluster['title'])}</h1>
        <p class="hero-text">{escape(coverage_summary_text(cluster))}</p>
        <div class="hero-stats">
          <article>
            <span class="stat-label">Reports</span>
            <strong>{cluster['story_count']}</strong>
          </article>
          <article>
            <span class="stat-label">Sources</span>
            <strong>{cluster['source_count']}</strong>
          </article>
          <article>
            <span class="stat-label">Sections</span>
            <strong>{cluster['section_count']}</strong>
          </article>
        </div>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="dual-grid">
        <article class="panel">
          <p class="panel-label">Lead Brief</p>
          <h2>Start with the strongest entry point</h2>
          {render_story_feature(cluster.get("lead_story"), "Lead Brief", "Open brief")}
        </article>
        <article class="panel">
          <p class="panel-label">Related Topics</p>
          <h2>Where this story line fits</h2>
          {render_topic_chip_row(related_topics) if related_topics else '<p>No topic tags are attached to this cluster yet.</p>'}
        </article>
      </div>
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Timeline</p>
          <h2>Related reports in chronological order</h2>
        </div>
        <p class="section-copy">
          Coverage pages are the closest thing the site has to a lightweight live-blog layout right now.
        </p>
      </div>
      <div class="timeline-list">
        {render_timeline(cluster.get("stories", []))}
      </div>
    </section>
    """

    return page_shell(
        title=f"{cluster['title']} | ShadowFetch Coverage",
        description=coverage_summary_text(cluster),
        canonical_path=cluster["path"],
        context=context,
        nav_current="topics",
        page_key="coverage",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Coverage pages group related reports so developing stories feel easier to follow across sources.",
    )


def render_archive_day_page(day: dict, model: dict, context: dict) -> str:
    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Archive Day</p>
        <h1>{escape(day['title'])}</h1>
        <p class="hero-text">Browse the briefs captured on this date and move back into sections, topics, or source pages from there.</p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Stories</p>
          <h2>{day['story_count']} brief{'s' if day['story_count'] != 1 else ''} on this day</h2>
        </div>
      </div>
      <div class="story-grid story-grid-archive">
        {render_story_grid(day.get("stories", []))}
      </div>
    </section>
    """

    return page_shell(
        title=f"{day['title']} | ShadowFetch Archive",
        description=f"Archive page for {day['title']} on ShadowFetch News.",
        canonical_path=day["path"],
        context=context,
        nav_current="archive",
        page_key="archive-day",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Archive day pages turn the front page into a more useful timeline.",
    )


def render_roundup_today_page(model: dict, context: dict) -> str:
    featured = model.get("featured", [])[:3]
    section_leads = [section["lead_story"] for section in model.get("sections", []) if section.get("lead_story")][:6]

    hero = f"""
    <section class="container hero hero-compact">
      <div class="hero-copy">
        <p class="eyebrow">Daily Roundup</p>
        <h1>Today’s editor-style package.</h1>
        <p class="hero-text">
          This page brings together the lead stories, strongest briefs, and the sections driving the day so the site feels less like a stream and more like a front page package.
        </p>
      </div>
    </section>
    """

    main_markup = f"""
    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Top Package</p>
          <h2>The stories setting the tone</h2>
        </div>
      </div>
      {render_featured_grid(featured)}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Editor’s Picks</p>
          <h2>Open these briefs first</h2>
        </div>
      </div>
      {render_editors_pick_grid(model.get("editors_picks", []))}
    </section>

    <section class="container page-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Desk Leaders</p>
          <h2>The lead from each section</h2>
        </div>
      </div>
      <div class="story-grid story-grid-archive">
        {render_story_grid(section_leads)}
      </div>
    </section>
    """

    return page_shell(
        title="Today’s Roundup | ShadowFetch News",
        description="The daily editor-style roundup from ShadowFetch News.",
        canonical_path="/roundups/today/",
        context=context,
        nav_current="latest",
        page_key="roundup",
        hero_markup=hero,
        main_markup=main_markup,
        footer_copy="Roundup pages give the site a stronger publication layer on top of the live feed.",
    )


def page_shell(
    *,
    title: str,
    description: str,
    canonical_path: str,
    context: dict,
    nav_current: str,
    page_key: str,
    hero_markup: str,
    main_markup: str,
    footer_copy: str,
    body_attrs: dict[str, str] | None = None,
) -> str:
    base_url = site_base_url()
    canonical_url = f"{base_url}{canonical_path}"
    body_attr_markup = " ".join(
        f'{escape(key)}="{escape(value)}"' for key, value in (body_attrs or {}).items()
    )
    body_prefix = f' data-page="{escape(page_key)}"'
    body_attr_string = f"{body_prefix} {body_attr_markup}".rstrip()
    og_image = OG_DEFAULT_IMAGE

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta name="theme-color" content="#071019">
  <link rel="canonical" href="{canonical_url}">
  <link rel="alternate" type="application/rss+xml" title="ShadowFetch News RSS" href="/feed.xml">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="ShadowFetch News">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{og_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(description)}">
  <meta name="twitter:image" content="{og_image}">
  <meta name="twitter:site" content="@MrBobCorbin">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;700&display=swap"
    rel="stylesheet"
  >
  <link rel="icon" href="/assets/shadowfetch-mark.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/styles.css">
  <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "NewsMediaOrganization",
      "name": "ShadowFetch News",
      "url": "{base_url}",
      "sameAs": [
        "{SOCIAL_X_URL}",
        "{SOCIAL_BLUESKY_URL}",
        "{SOCIAL_KALSHI_URL}"
      ]
    }}
  </script>
</head>
<body{body_attr_string}>
  <div class="page-orb orb-left" aria-hidden="true"></div>
  <div class="page-orb orb-right" aria-hidden="true"></div>

  {render_site_header(context, nav_current)}

  <main>
    {hero_markup}
    {main_markup}
  </main>

  {render_site_footer(footer_copy)}
  {render_mobile_dock(nav_current)}
  <script src="/assets/app.js"></script>
</body>
</html>
"""


def render_site_header(context: dict, nav_current: str) -> str:
    return f"""
  <header class="site-chrome">
    <div class="utility-bar">
      <div class="container utility-wrap">
        <div class="utility-pill">
          <span class="utility-label">Visitor Counter</span>
          <strong data-visit-count>{context['visit_count']}</strong>
        </div>
        <div class="utility-pill utility-status">
          <span class="utility-label">Updated</span>
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
          {render_nav_link("/", "Front Page", nav_current == "home")}
          {render_nav_link("/latest/", "Late Breaking", nav_current == "latest")}
          {render_nav_link("/sections/", "Sections", nav_current == "sections")}
          {render_nav_link("/topics/", "Topics", nav_current == "topics")}
          {render_nav_link("/search/", "Search", nav_current == "search")}
          {render_nav_link("/about/", "About", nav_current == "about")}
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
"""


def render_site_footer(footer_copy: str) -> str:
    return f"""
  <footer class="site-footer">
    <div class="container footer-wrap">
      <div>
        <p class="footer-title">ShadowFetch News</p>
        <p class="footer-copy">{escape(footer_copy)}</p>
      </div>
      <div class="footer-links">
        <a href="/latest/">Latest</a>
        <a href="/topics/">Topics</a>
        <a href="/sources/">Sources</a>
        <a href="/archive/">Archive</a>
        <a href="/about/">About</a>
      </div>
    </div>
  </footer>
"""


def render_mobile_dock(nav_current: str) -> str:
    return f"""
  <nav class="mobile-dock" aria-label="Mobile">
    {render_mobile_link("/", "Front", nav_current == "home")}
    {render_mobile_link("/latest/", "Latest", nav_current == "latest")}
    {render_mobile_link("/topics/", "Topics", nav_current == "topics")}
    {render_mobile_link("/search/", "Search", nav_current == "search")}
    {render_mobile_link("/sections/", "Sections", nav_current == "sections")}
  </nav>
"""


def render_nav_link(href: str, label: str, active: bool) -> str:
    aria = ' aria-current="page"' if active else ""
    return f'<a href="{href}"{aria}>{escape(label)}</a>'


def render_mobile_link(href: str, label: str, active: bool) -> str:
    active_class = " mobile-active" if active else ""
    aria = ' aria-current="page"' if active else ""
    return f'<a class="mobile-link{active_class}" href="{href}"{aria}>{escape(label)}</a>'


def render_search_form(query: str, variant: str) -> str:
    variant_class = f"search-form-{variant}"
    return f"""
    <form class="search-form {variant_class}" action="/search/" method="get" data-search-form>
      <label class="visually-hidden" for="search-input-{variant}">Search ShadowFetch News</label>
      <input
        class="search-input"
        id="search-input-{variant}"
        type="search"
        name="q"
        placeholder="Search briefs, topics, sources, people, places..."
        value="{escape(query)}"
        data-search-input
      >
      <button class="button button-secondary search-submit" type="submit">Search</button>
    </form>
    """


def render_featured_grid(stories: list[dict]) -> str:
    if not stories:
        return '<p class="empty-card">Featured stories are not available yet.</p>'

    lead = stories[0]
    side = stories[1:3]
    rail = stories[3] if len(stories) > 3 else None
    side_markup = "".join(
        render_story_snippet(story, "feature-snippet") for story in side
    )
    rail_markup = render_story_snippet(rail, "rail-story") if rail else '<p class="empty-card">The next featured layer will appear here on refresh.</p>'

    return f"""
    <div class="frontline-shell">
      {render_story_feature(lead, "Lead Brief", "Open brief")}
      <div class="feature-stack">{side_markup}</div>
      <aside class="panel briefing-rail">
        <p class="panel-label">Next Up</p>
        <h2>Another strong story line to watch</h2>
        {rail_markup}
        <div class="stack-links">
          <a class="social-panel-link" href="/roundups/today/">
            <span>Roundup</span>
            <strong>Open today’s editor package</strong>
          </a>
          <a class="social-panel-link" href="/topics/">
            <span>Topics</span>
            <strong>Track the bigger threads</strong>
          </a>
        </div>
      </aside>
    </div>
    """


def render_story_feature(story: dict | None, label: str, cta_label: str) -> str:
    if not story:
        return '<p class="empty-card">A featured story will appear here when the feed refreshes.</p>'

    return f"""
    <article class="feature-lead">
      <p class="panel-label">{escape(label)}</p>
      {story_meta_markup(story)}
      <h2><a class="story-headline-link" href="{story['brief_path']}">{escape(story['title'])}</a></h2>
      <p>{escape(story['summary'])}</p>
      {render_topic_chip_row(story.get("topics", [])[:3]) if story.get("topics") else ""}
      <div class="story-actions">
        <a class="story-link" href="{story['brief_path']}">{escape(cta_label)}</a>
        <a class="story-source-link" href="{story['link']}" target="_blank" rel="noreferrer noopener">Original source</a>
      </div>
    </article>
    """


def render_story_snippet(story: dict | None, class_name: str) -> str:
    if not story:
        return '<p class="empty-card">This slot will fill on the next update.</p>'
    return f"""
    <article class="{escape(class_name)}">
      {story_meta_markup(story)}
      <h3><a class="story-headline-link" href="{story['brief_path']}">{escape(story['title'])}</a></h3>
      <p>{escape(story['summary'])}</p>
      <div class="story-actions">
        <a class="story-link" href="{story['brief_path']}">Open brief</a>
        <a class="story-source-link" href="{story['link']}" target="_blank" rel="noreferrer noopener">Source</a>
      </div>
    </article>
    """


def render_quicklink_card(title: str, body: str, href: str) -> str:
    return f"""
    <article class="quicklink-card">
      <p class="panel-label">{escape(title)}</p>
      <h3>{escape(title)}</h3>
      <p>{escape(body)}</p>
      <a class="story-link" href="{href}">Open page</a>
    </article>
    """


def render_developing_grid(coverage_clusters: list[dict], fallback_topics: list[dict]) -> str:
    cards = []
    for cluster in coverage_clusters[:6]:
        cards.append(
            f"""
            <article class="developing-card">
              <p class="panel-label">Developing Story</p>
              <h3><a class="story-headline-link" href="{cluster['path']}">{escape(cluster['title'])}</a></h3>
              <p>{escape(coverage_summary_text(cluster))}</p>
              <div class="developing-stats">
                <span>{cluster['story_count']} reports</span>
                <span>{cluster['source_count']} sources</span>
                <span>{cluster['section_count']} sections</span>
              </div>
              <div class="story-actions">
                <a class="story-link" href="{cluster['path']}">Open coverage</a>
                <a class="story-source-link" href="{cluster['lead_story']['brief_path']}">Lead brief</a>
              </div>
            </article>
            """
        )

    if len(cards) < 3:
        for topic in fallback_topics:
            if topic.get("story_count", 0) < 2:
                continue
            cards.append(
                f"""
                <article class="developing-card">
                  <p class="panel-label">Topic Watch</p>
                  <h3><a class="story-headline-link" href="{topic['path']}">{escape(topic['title'])}</a></h3>
                  <p>{escape(topic.get('description', ''))}</p>
                  <div class="developing-stats">
                    <span>{topic['story_count']} stories</span>
                    <span>Topic page</span>
                  </div>
                  <div class="story-actions">
                    <a class="story-link" href="{topic['path']}">Open topic</a>
                  </div>
                </article>
                """
            )
            if len(cards) >= 6:
                break

    if not cards:
        return '<p class="empty-card">Developing story groupings will appear here as coverage overlaps.</p>'

    return f'<div class="developing-grid">{"".join(cards)}</div>'


def render_editors_pick_grid(picks: list[dict]) -> str:
    if not picks:
        return '<p class="empty-card">Editor picks will appear here once the feed has enough variety.</p>'

    cards = []
    for story in picks:
        cards.append(
            f"""
            <article class="editor-card">
              {story_meta_markup(story)}
              <h3><a class="story-headline-link" href="{story['brief_path']}">{escape(story['title'])}</a></h3>
              <p>{escape(story['why_it_matters'])}</p>
              <div class="story-actions">
                <a class="story-link" href="{story['brief_path']}">Open brief</a>
                <a class="story-source-link" href="{story['link']}" target="_blank" rel="noreferrer noopener">Source</a>
              </div>
            </article>
            """
        )
    return f'<div class="editor-grid">{"".join(cards)}</div>'


def render_topic_grid(topics: list[dict], large: bool = False) -> str:
    if not topics:
        return '<p class="empty-card">Topic pages will appear here when the feed begins matching broader story lines.</p>'

    class_name = "topic-grid topic-grid-large" if large else "topic-grid"
    return f'<div class="{class_name}">{"".join(render_topic_card(topic) for topic in topics)}</div>'


def render_topic_card(topic: dict) -> str:
    lead_story = topic.get("lead_story")
    lead_markup = (
        f'<p class="topic-lead">{escape(lead_story["title"])}</p>'
        if lead_story
        else '<p class="topic-lead">Waiting for a lead story.</p>'
    )
    return f"""
    <article class="topic-card">
      <p class="panel-label">Topic Page</p>
      <h3><a class="story-headline-link" href="{topic['path']}">{escape(topic['title'])}</a></h3>
      <p>{escape(topic.get('description', ''))}</p>
      {lead_markup}
      <div class="developing-stats">
        <span>{topic['story_count']} stories</span>
      </div>
      <div class="story-actions">
        <a class="story-link" href="{topic['path']}">Open topic</a>
      </div>
    </article>
    """


def render_section_overview_grid(sections: list[dict], story_limit: int) -> str:
    cards = []
    for section in sections:
        cards.append(
            f"""
            <article class="section-card">
              <p class="panel-label">{escape(section.get('short_label', section['title']))}</p>
              <h3>{escape(section['title'])}</h3>
              <p>{escape(section.get('description', ''))}</p>
              <div class="story-list">
                {''.join(render_compact_story(story) for story in section.get('stories', [])[:story_limit]) or '<p class="empty-card">No stories available right now.</p>'}
              </div>
              <div class="story-actions">
                <a class="story-link" href="{section['path']}">Open desk</a>
              </div>
            </article>
            """
        )
    return f'<div class="coverage-grid">{"".join(cards)}</div>'


def render_source_directory(sources: list[dict], compact: bool = False) -> str:
    return "".join(render_source_directory_card(source, compact) for source in sources)


def render_source_directory_card(source: dict, compact: bool = False) -> str:
    class_name = "source-directory-card source-directory-card-compact" if compact else "source-directory-card"
    sections_markup = "".join(
        f'<a class="source-chip" href="{section["path"]}">{escape(section["short_label"])}</a>'
        for section in source.get("sections", [])[:4]
    )
    return f"""
    <article class="{class_name}">
      <p class="panel-label">Source Page</p>
      <h3><a class="story-headline-link" href="{source['path']}">{escape(source['name'])}</a></h3>
      <p>{escape(source_summary_text(source))}</p>
      <div class="source-row">{sections_markup}</div>
      <div class="story-actions">
        <a class="story-link" href="{source['path']}">Open source</a>
        <a class="story-source-link" href="{safe_url(source.get('homepage', ''))}" target="_blank" rel="noreferrer noopener">Source site</a>
      </div>
    </article>
    """


def render_source_wall(sources: list[dict]) -> str:
    return "".join(
        f"""
        <a class="source-card" href="{source['path']}">
          <span class="source-label">Source Page</span>
          <strong>{escape(source['name'])}</strong>
          <small>{escape(source_summary_text(source))}</small>
        </a>
        """
        for source in sources
    )


def render_archive_directory(days: list[dict]) -> str:
    if not days:
        return '<p class="empty-card">Archive pages will appear here as stories are collected into dated sets.</p>'
    return f"""
    <div class="date-grid">
      {''.join(render_archive_day_card(day) for day in days)}
    </div>
    """


def render_archive_day_card(day: dict) -> str:
    lead_story = day.get("stories", [None])[0]
    lead_text = lead_story["title"] if lead_story else "No lead story available."
    return f"""
    <article class="date-card">
      <p class="panel-label">Archive Day</p>
      <h3><a class="story-headline-link" href="{day['path']}">{escape(day['title'])}</a></h3>
      <p>{escape(lead_text)}</p>
      <div class="developing-stats">
        <span>{day['story_count']} stories</span>
      </div>
      <div class="story-actions">
        <a class="story-link" href="{day['path']}">Open day</a>
      </div>
    </article>
    """


def render_filter_toolbar(sections: list[dict], toolbar_id: str, grid_id: str, summary_id: str) -> str:
    buttons = [
        filter_button_markup("all", "All Stories", True),
        *[
            filter_button_markup(section["key"], section.get("short_label", section["title"]), False)
            for section in sections
        ],
    ]
    return (
        f'<div class="toolbar" id="{toolbar_id}" data-filter-toolbar data-target-grid="{grid_id}" data-summary-id="{summary_id}">'
        + "".join(buttons)
        + "</div>"
    )


def filter_button_markup(key: str, label: str, pressed: bool) -> str:
    return (
        f'<button class="filter-pill" type="button" data-filter-key="{escape(key)}" '
        f'data-filter-label="{escape(label)}" aria-pressed="{"true" if pressed else "false"}">{escape(label)}</button>'
    )


def render_story_grid(stories: list[dict]) -> str:
    if not stories:
        return '<p class="empty-card">The story collection is temporarily empty.</p>'
    return "".join(story_card_markup(story) for story in stories)


def story_card_markup(story: dict) -> str:
    return f"""
    <article class="story-card" data-section-key="{escape(story.get('section_key', ''))}">
      {story_meta_markup(story)}
      <h3><a class="story-headline-link" href="{story['brief_path']}">{escape(story['title'])}</a></h3>
      <p>{escape(story['summary'])}</p>
      {render_topic_chip_row(story.get("topics", [])[:2]) if story.get("topics") else ""}
      <div class="story-actions">
        <a class="story-link" href="{story['brief_path']}">Open brief</a>
        <a class="story-source-link" href="{story['link']}" target="_blank" rel="noreferrer noopener">Original source</a>
        <span class="story-reading-time">{story.get('reading_time', '')}</span>
      </div>
    </article>
    """


def render_compact_story(story: dict) -> str:
    return f"""
    <article class="story-compact">
      <div class="story-meta">
        <a class="story-source" href="{story['source_path']}">{escape(story['source'])}</a>
        <span class="story-time">{escape(story['display_time'])}</span>
      </div>
      <h3><a class="story-headline-link" href="{story['brief_path']}">{escape(story['title'])}</a></h3>
      <div class="story-actions">
        <a class="story-link" href="{story['brief_path']}">Open brief</a>
      </div>
    </article>
    """


def render_timeline(stories: list[dict]) -> str:
    if not stories:
        return '<p class="empty-card">The timeline is empty right now.</p>'
    return "".join(
        f"""
        <article class="timeline-item">
          <div class="story-meta">
            <a class="story-tag" href="{story['section_path']}">{escape(story['section'])}</a>
            <a class="story-source" href="{story['source_path']}">{escape(story['source'])}</a>
            <span class="story-time">{escape(story['display_time'])}</span>
            <span class="story-recency {escape(story['recency_class'])}">{escape(story['relative_time'])}</span>
          </div>
          <h3><a class="story-headline-link" href="{story['brief_path']}">{escape(story['title'])}</a></h3>
          <p>{escape(story['summary'])}</p>
          <div class="story-actions">
            <a class="story-link" href="{story['brief_path']}">Open brief</a>
            <a class="story-source-link" href="{story['link']}" target="_blank" rel="noreferrer noopener">Original source</a>
          </div>
        </article>
        """
        for story in stories
    )


def render_topic_chip_row(topics: Iterable[dict]) -> str:
    topic_list = list(topics)
    if not topic_list:
        return ""
    return '<div class="chip-row">' + "".join(
        f'<a class="topic-chip" href="{topic["path"]}">{escape(topic["title"])}</a>'
        for topic in topic_list
    ) + "</div>"


def render_source_row_from_configs(sources: list[dict]) -> str:
    return "".join(
        f'<a class="source-chip" href="/sources/{slugify(source.get("name", "source"))}/">{escape(source.get("name", "Source"))}</a>'
        for source in sources
    )


def story_meta_markup(story: dict) -> str:
    badge = ""
    if story.get("is_breaking"):
        badge = '<span class="story-badge badge-breaking">BREAKING</span>'
    elif story.get("is_new"):
        badge = '<span class="story-badge badge-new">NEW</span>'
    return f"""
      <div class="story-meta">
        {badge}
        <a class="story-tag" href="{story['section_path']}">{escape(story.get('section', 'General'))}</a>
        <a class="story-source" href="{story['source_path']}">{escape(story.get('source', 'Source'))}</a>
        <span class="story-time">{escape(story.get('display_time', ''))}</span>
        <span class="story-recency {escape(story.get('recency_class', ''))}">{escape(story.get('relative_time', ''))}</span>
      </div>
"""


def render_breaking_ticker(stories: list[dict], limit: int) -> str:
    if not stories:
        return '<span class="ticker-placeholder">Breaking headlines are temporarily unavailable.</span>'

    items = [
        f'<a class="ticker-item" href="{story["brief_path"]}"><span>{escape(story.get("title", "Untitled story"))}</span></a>'
        for story in stories[:limit]
    ]
    content = '\n<span class="ticker-divider" aria-hidden="true">•</span>\n'.join(items)
    divider = '\n<span class="ticker-divider" aria-hidden="true">•</span>\n'
    return f"{content}{divider}{content}"


def render_story_summary(stories: list[dict], limit: int) -> str:
    count = min(len(stories), limit)
    return f"Showing {count} {'story' if count == 1 else 'stories'} across every section in this view."


def build_why_it_matters(story: dict, topics_by_key: dict[str, dict]) -> str:
    section_context = SECTION_CONTEXT.get(
        story.get("section_key", ""),
        "It connects to a broader part of the news cycle and is likely to keep generating follow-on coverage.",
    )
    topic_names = [
        topics_by_key[topic_key]["title"]
        for topic_key in story.get("topic_keys", [])[:2]
        if topic_key in topics_by_key
    ]
    if topic_names:
        if len(topic_names) == 1:
            topic_line = f" ShadowFetch is also tracking it through the {topic_names[0]} topic page."
        else:
            topic_line = f" ShadowFetch is also tracking it through {topic_names[0]} and {topic_names[1]}."
    else:
        topic_line = ""
    return f"{section_context}{topic_line}"


def coverage_summary_text(cluster: dict) -> str:
    return (
        f"Tracking {cluster['story_count']} related reports across {cluster['source_count']} "
        f"{'source' if cluster['source_count'] == 1 else 'sources'}, anchored by the lead story now surfacing on the site."
    )


def source_summary_text(source: dict) -> str:
    section_names = ", ".join(section["short_label"] for section in source.get("sections", [])[:4])
    if section_names:
        return f"Appearing across {section_names}, with {source['story_count']} recent {'story' if source['story_count'] == 1 else 'stories'} on the site."
    return f"{source['story_count']} recent {'story' if source['story_count'] == 1 else 'stories'} on the site."


def related_topics_for_stories(stories: list[dict], topics_by_key: dict[str, dict]) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for story in stories:
        for topic_key in story.get("topic_keys", []):
            counts[topic_key] += 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [topics_by_key[key] for key, _count in ordered if key in topics_by_key]


def related_stories_for_brief(story: dict, model: dict) -> list[dict]:
    related = []
    seen_ids = {story["id"]}
    for candidate in model.get("stories", []):
        if candidate["id"] in seen_ids:
            continue
        if candidate.get("section_key") == story.get("section_key") or set(candidate.get("topic_keys", [])) & set(story.get("topic_keys", [])):
            related.append(candidate)
            seen_ids.add(candidate["id"])
        if len(related) >= 6:
            break
    return related


def story_matches_topic(story: dict, topic: dict) -> bool:
    haystack = f"{story.get('title', '')} {story.get('summary', '')}".lower()
    return any(keyword.lower() in haystack for keyword in topic.get("keywords", []))


def significant_tokens(text: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 4 and token not in STOPWORDS
    }
    return tokens


def story_identity(story: dict) -> str:
    link = normalize_story_url(story.get("link", ""))
    if link:
        return link
    source = story.get("source_key") or slugify(story.get("source", ""))
    return f"{source}:{normalize_title(story.get('title', ''))}"


def normalize_story_url(url: str) -> str:
    try:
        parsed = parse.urlparse(url)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"}:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"


def normalize_title(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


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


def format_relative_time(value: str | None) -> str:
    parsed = parse_timestamp(value)
    now = datetime.now(timezone.utc)
    delta = now - parsed
    total_minutes = max(int(delta.total_seconds() // 60), 0)

    if total_minutes < 5:
        return "Just in"
    if total_minutes < 60:
        return f"{total_minutes} min ago"

    total_hours = total_minutes // 60
    if total_hours < 24:
        return f"{total_hours} hr ago"

    total_days = total_hours // 24
    return f"{total_days} day{'s' if total_days != 1 else ''} ago"


def recency_class(value: str | None) -> str:
    parsed = parse_timestamp(value)
    now = datetime.now(timezone.utc)
    delta = now - parsed
    total_minutes = max(int(delta.total_seconds() // 60), 0)

    if total_minutes < 15:
        return "story-recency-hot"
    if total_minutes < 180:
        return "story-recency-warm"
    return "story-recency-cool"


def is_breaking_story(value: str | None) -> bool:
    """True if the story was published within the last 15 minutes."""
    from datetime import datetime, timezone
    parsed = parse_timestamp(value)
    now = datetime.now(timezone.utc)
    delta = now - parsed
    return delta.total_seconds() < 900  # 15 min


def is_new_story(value: str | None) -> bool:
    """True if the story was published within the last 2 hours."""
    from datetime import datetime, timezone
    parsed = parse_timestamp(value)
    now = datetime.now(timezone.utc)
    delta = now - parsed
    return delta.total_seconds() < 7200  # 2 hr


def estimate_reading_time(title: str, summary: str) -> str:
    """Estimate reading time based on brief word count."""
    words = len((title + " " + summary).split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"


def format_archive_date(date_key: str) -> str:
    parsed = datetime.fromisoformat(date_key)
    month = parsed.strftime("%b")
    day = str(parsed.day)
    year = parsed.strftime("%Y")
    return f"{month} {day}, {year}"


def format_integer(value: int) -> str:
    return f"{value:,}"


def site_base_url() -> str:
    return f"https://{CNAME_PATH.read_text(encoding='utf-8').strip()}"


def safe_url(url: str) -> str:
    try:
        parsed = parse.urlparse(url)
        return url if parsed.scheme in {"http", "https"} else "#"
    except Exception:
        return "#"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


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
