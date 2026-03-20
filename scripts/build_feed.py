#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "assets" / "data" / "feed-config.json"
OUTPUT_PATH = ROOT / "assets" / "data" / "feed.json"
USER_AGENT = "ShadowFetchNewsBot/1.0 (+https://www.shadowfetch.com)"


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    per_section_limit = int(config.get("per_section_limit", 8))
    latest_limit = int(config.get("latest_limit", 30))
    featured_limit = int(config.get("featured_limit", 3))

    sections = []
    all_stories: List[Dict[str, str]] = []
    successful_sources = 0
    total_sources = 0

    for section in config.get("sections", []):
        sources = section.get("sources", [])
        total_sources += len(sources)

        section_stories: List[Dict[str, str]] = []
        section_successes = 0

        for source in sources:
            try:
                stories = fetch_feed(
                    source=source,
                    section=section,
                    source_item_limit=int(source.get("item_limit", config.get("source_item_limit", 10))),
                )
            except Exception:
                stories = []

            if stories:
                section_successes += 1
                successful_sources += 1
                section_stories.extend(stories)

        deduped = dedupe_stories(section_stories)
        deduped.sort(key=lambda story: story["timestamp"], reverse=True)
        limited = deduped[: int(section.get("story_limit", per_section_limit))]
        all_stories.extend(limited)

        sections.append(
            {
                "key": section["key"],
                "title": section["title"],
                "short_label": section.get("short_label", section["title"]),
                "description": section.get("description", ""),
                "successful_sources": section_successes,
                "total_sources": len(sources),
                "stories": limited,
            }
        )

    latest = dedupe_stories(all_stories)
    latest.sort(key=lambda story: story["timestamp"], reverse=True)
    latest = latest[:latest_limit]

    payload = {
      "generated_at": now_iso(),
      "successful_sources": successful_sources,
      "total_sources": total_sources,
      "featured": latest[:featured_limit],
      "latest": latest,
      "sections": sections,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fetch_feed(source: Dict[str, str], section: Dict[str, str], source_item_limit: int) -> List[Dict[str, str]]:
    request = Request(
        source["url"],
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )

    with urlopen(request, timeout=20) as response:
        raw_bytes = response.read()

    root = ET.fromstring(raw_bytes)
    entries = parse_entries(root)
    stories = []

    for entry in entries[:source_item_limit]:
        link = safe_url(extract_link(entry))
        if not link:
            continue

        published = extract_text(entry, ["pubDate", "published", "updated", "date"]) or now_iso()
        timestamp = parse_timestamp(published)
        summary = summarize(strip_html(extract_summary(entry)))

        stories.append(
            {
                "title": extract_text(entry, ["title"]) or "Untitled story",
                "link": link,
                "summary": summary or "Open the original source for the full story.",
                "source": source["name"],
                "section": section["title"],
                "section_key": section["key"],
                "timestamp": timestamp,
            }
        )

    return stories


def parse_entries(root: ET.Element) -> List[ET.Element]:
    channel = first_direct_child(root, "channel")
    if channel is not None:
        return [child for child in list(channel) if local_name(child.tag) == "item"]

    return [child for child in list(root) if local_name(child.tag) == "entry"]


def extract_summary(entry: ET.Element) -> str:
    return (
        extract_text(entry, ["description", "summary", "content", "encoded"])
        or "Open the original source for the full story."
    )


def extract_link(entry: ET.Element) -> str:
    for child in list(entry):
        if local_name(child.tag) != "link":
            continue

        href = (child.attrib.get("href") or "").strip()
        rel = (child.attrib.get("rel") or "").strip()
        if href and (not rel or rel == "alternate"):
            return href

        if child.text and child.text.strip():
            return child.text.strip()

    return ""


def extract_text(entry: ET.Element, names: List[str]) -> str:
    name_set = {name.lower() for name in names}
    for child in list(entry):
        if local_name(child.tag).lower() in name_set:
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return ""


def first_direct_child(node: ET.Element, name: str) -> Optional[ET.Element]:
    for child in list(node):
        if local_name(child.tag) == name:
            return child
    return None


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def strip_html(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def summarize(text: str) -> str:
    if len(text) <= 180:
        return text
    return f"{text[:177].strip()}..."


def dedupe_stories(stories: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    unique = []
    for story in stories:
        key = story.get("link") or f"{story.get('source', '')}:{story.get('title', '')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(story)
    return unique


def parse_timestamp(value: str) -> str:
    for parser in (parse_email_date, parse_iso_date, parse_custom_date):
        parsed = parser(value)
        if parsed:
            return parsed
    return now_iso()


def parse_email_date(value: str) -> Optional[str]:
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, IndexError):
        return None


def parse_iso_date(value: str) -> Optional[str]:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_custom_date(value: str) -> Optional[str]:
    match = re.match(r"^[A-Za-z]{3},\s*(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2}):(\d{2})", value)
    if not match:
        return None

    month, day, year, hour, minute = (int(part) for part in match.groups())
    parsed = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def safe_url(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        return ""
    return value


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()
