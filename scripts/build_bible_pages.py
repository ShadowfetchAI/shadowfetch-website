#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import html
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import request
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DATA = ROOT / "assets" / "data"
READINGS_DIR = ASSETS_DATA / "bible-readings"
SOURCE_CACHE_DIR = ROOT / "content" / "bible-source-cache"

SUMMARY_PATH = ASSETS_DATA / "bible-edition.json"
INDEX_PATH = ROOT / "index.html"
BIBLE_PATH = ROOT / "bible" / "index.html"
CALENDAR_PATH = ROOT / "calendar" / "index.html"
ARCHIVE_PATH = ROOT / "archive" / "index.html"
SETTINGS_PATH = ROOT / "settings" / "index.html"
SIGNUP_PATH = ROOT / "signup" / "index.html"
THANKS_PATH = ROOT / "blessed" / "index.html"
MANIFEST_PATH = ROOT / "manifest.webmanifest"
SERVICE_WORKER_PATH = ROOT / "service-worker.js"

BASE_URL = "https://www.shadowfetch.com"
SITE_TITLE = "Shadowfetch: Bible Edition"
SITE_SHORT_NAME = "Shadowfetch Bible"
TAGLINE = "Fetch the Word. Abide in the Shadow."
SITE_DESCRIPTION = (
    "A calm, protective daily Bible-reading companion with complete chapters, one simple email a day, "
    "and a newspaper-inspired devotional layout built around Psalm 91."
)
PSALM_91 = "He who dwells in the shelter of the Most High will abide in the shadow of the Almighty."
BUY_ME_A_COFFEE_URL = "https://www.buymeacoffee.com/shadowfetch"
THEME_COLOR = "#05070A"
DEFAULT_CANON = "protestant"
TOTAL_DAYS = 365

BRAND_NAME = "Shadowfetch"
BRAND_DIVISION = "AI Engineering"
BRAND_TAGLINE = "Precision. Reliability. Architectural Excellence."
BRAND_DESCRIPTION = (
    "Shadowfetch builds mission-critical Web and iOS applications for organizations that demand "
    "technical perfection and AI-native architecture."
)
BRAND_OG_IMAGE = "shadowfetch-crest.jpg"
CONTACT_EMAIL = "RobertCorbin84@gmail.com"
FOUNDER_X_HANDLE = "@MrBobCorbin"
CEO_X_HANDLE = "@Kaitlancorbin1"
FOUNDER_X_URL = "https://x.com/MrBobCorbin"
CEO_X_URL = "https://x.com/Kaitlancorbin1"
FOOTER_INQUIRY_BODY = "Project summary:\nObjectives:\nTimeline:\n"
GENERAL_INQUIRY_BODY = "Project summary:\nObjectives:\nConstraints:\nTimeline:\n"
ENGAGEMENT_INQUIRY_BODY = "Project summary:\nBusiness objective:\nTechnical constraints:\nDesired timeline:\n"

KJV_CONTENTS_URL = "https://api.github.com/repos/aruljohn/Bible-kjv/contents"
DRA_URL = "https://raw.githubusercontent.com/xxruyle/Bible-DouayRheims/main/EntireBible-DR.json"

KJV_CACHE_PATH = SOURCE_CACHE_DIR / "kjv-normalized.json"
DRA_CACHE_PATH = SOURCE_CACHE_DIR / "douay-rheims-normalized.json"

REFLECTION_TEMPLATES = [
    "Let this verse be the quieter voice that sets the pace for the rest of the day.",
    "Read this line twice and let it slow the room down before anything else speaks.",
    "This is the kind of sentence to keep near when the day feels louder than your prayers.",
    "Hold this verse close and let its steadiness shape the next few hours.",
    "Sometimes the holiest thing is staying with one clear line until your heart catches up to it.",
    "Let this passage feel like lamp light: warm enough to guide, gentle enough to rest in.",
    "Read it without rushing. The comfort is in the staying, not the sprinting.",
    "Carry this line with you and let it soften the edges of whatever waits today.",
    "This verse is a good place to begin when you need calm before clarity.",
    "Come back to this sentence tonight and see what it held together for you.",
    "Let this be the sheltering word of the day: small enough to remember, strong enough to keep.",
    "If the day gets scattered, return here and let this verse gather you again.",
]

ENCOURAGEMENT_ITEMS = [
    {
        "title": "One calm reading at a time",
        "summary": "The plan keeps the pace gentle: complete chapters, clear progress, and no pressure to perform.",
    },
    {
        "title": "A quiet catch-up rhythm",
        "summary": "Missed days surface softly so readers can return without shame and keep moving with grace.",
    },
    {
        "title": "Free forever",
        "summary": "Every chapter stays open on the web. The only ask is a voluntary coffee if someone wants to keep the emails going.",
    },
]

CANON_CHOICES = [
    {
        "key": "protestant",
        "label": "Protestant",
        "summary": "66 books - KJV style",
        "translation": "King James Version",
    },
    {
        "key": "catholic",
        "label": "Roman Catholic",
        "summary": "73 books - Douay-Rheims / CPDV style",
        "translation": "Douay-Rheims",
    },
]

PROTESTANT_TRACKS = {
    "history": [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numbers",
        "Deuteronomy",
        "Joshua",
        "Judges",
        "Ruth",
        "1 Samuel",
        "2 Samuel",
        "1 Kings",
        "2 Kings",
        "1 Chronicles",
        "2 Chronicles",
        "Ezra",
        "Nehemiah",
        "Esther",
    ],
    "wisdom": ["Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon"],
    "prophets": [
        "Isaiah",
        "Jeremiah",
        "Lamentations",
        "Ezekiel",
        "Daniel",
        "Hosea",
        "Joel",
        "Amos",
        "Obadiah",
        "Jonah",
        "Micah",
        "Nahum",
        "Habakkuk",
        "Zephaniah",
        "Haggai",
        "Zechariah",
        "Malachi",
    ],
    "new_testament": [
        "Matthew",
        "Mark",
        "Luke",
        "John",
        "Acts",
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "Philippians",
        "Colossians",
        "1 Thessalonians",
        "2 Thessalonians",
        "1 Timothy",
        "2 Timothy",
        "Titus",
        "Philemon",
        "Hebrews",
        "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        "Revelation",
    ],
}

CATHOLIC_TRACKS = {
    "history": [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numbers",
        "Deuteronomy",
        "Josue",
        "Judges",
        "Ruth",
        "1 Kings",
        "2 Kings",
        "3 Kings",
        "4 Kings",
        "1 Paralipomenon",
        "2 Paralipomenon",
        "1 Esdras",
        "2 Esdras",
        "Tobias",
        "Judith",
        "Esther",
        "1 Machabees",
        "2 Machabees",
    ],
    "wisdom": [
        "Job",
        "Psalms",
        "Proverbs",
        "Ecclesiastes",
        "Canticles",
        "Wisdom",
        "Ecclesiasticus",
    ],
    "prophets": [
        "Isaias",
        "Jeremias",
        "Lamentations",
        "Baruch",
        "Ezechiel",
        "Daniel",
        "Osee",
        "Joel",
        "Amos",
        "Abdias",
        "Jonas",
        "Micheas",
        "Nahum",
        "Habacuc",
        "Sophonias",
        "Aggeus",
        "Zacharias",
        "Malachias",
    ],
    "new_testament": [
        "Matthew",
        "Mark",
        "Luke",
        "John",
        "Acts",
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "Philippians",
        "Colossians",
        "1 Thessalonians",
        "2 Thessalonians",
        "1 Timothy",
        "2 Timothy",
        "Titus",
        "Philemon",
        "Hebrews",
        "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        "Apocalypse",
    ],
}

QUOTE_PREFERRED_BOOKS = (
    "Psalms",
    "Proverbs",
    "Ecclesiastes",
    "Canticles",
    "Song of Solomon",
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Romans",
    "James",
)


def main() -> None:
    datasets = load_source_datasets()
    plans = {
        "protestant": build_plan(
            canon_key="protestant",
            canon_label="Protestant",
            translation_name="King James Version",
            books=datasets["protestant"],
            tracks=PROTESTANT_TRACKS,
        ),
        "catholic": build_plan(
            canon_key="catholic",
            canon_label="Roman Catholic",
            translation_name="Douay-Rheims",
            books=datasets["catholic"],
            tracks=CATHOLIC_TRACKS,
        ),
    }
    for plan in plans.values():
        validate_plan(plan)

    payload = build_summary_payload(plans)

    ASSETS_DATA.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_day_payloads(plans)

    write_page(INDEX_PATH, render_home_page(payload))
    write_page(BIBLE_PATH, render_bible_page(payload))
    write_page(CALENDAR_PATH, render_retired_page("Reading Rhythm", "/calendar/"))
    write_page(ARCHIVE_PATH, render_retired_page("Archive", "/archive/"))
    write_page(SETTINGS_PATH, render_settings_page(payload))
    write_page(SIGNUP_PATH, render_signup_page(payload))
    write_page(THANKS_PATH, render_thanks_page())

    MANIFEST_PATH.write_text(build_manifest(), encoding="utf-8")
    SERVICE_WORKER_PATH.write_text(build_service_worker(), encoding="utf-8")


def write_page(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def compute_asset_version() -> str:
    digest = hashlib.sha1()
    for relative_path in ("assets/styles.css", "assets/app.js", "assets/shadowfetch-mark.svg", f"assets/{BRAND_OG_IMAGE}"):
        digest.update((ROOT / relative_path).read_bytes())
    return digest.hexdigest()[:12]


ASSET_VERSION = compute_asset_version()


def asset_url(filename: str) -> str:
    return f"/assets/{filename}?v={ASSET_VERSION}"


def mailto_url(subject: str, body: str = "") -> str:
    query_parts = [f"subject={quote(subject)}"]
    if body:
        query_parts.append(f"body={quote(body)}")
    return f"mailto:{CONTACT_EMAIL}?{'&'.join(query_parts)}"


def fetch_json(url: str) -> Any:
    req = request.Request(url, headers={"User-Agent": "Shadowfetch Bible Builder/1.0"})
    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\n", " ").strip())


def word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def load_source_datasets() -> dict[str, dict[str, list[dict[str, Any]]]]:
    SOURCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "protestant": load_kjv_books(),
        "catholic": load_douay_rheims_books(),
    }


def load_kjv_books() -> dict[str, list[dict[str, Any]]]:
    if KJV_CACHE_PATH.exists():
        return json.loads(KJV_CACHE_PATH.read_text(encoding="utf-8"))

    listing = fetch_json(KJV_CONTENTS_URL)
    books: dict[str, list[dict[str, Any]]] = {}
    for entry in listing:
        download_url = entry.get("download_url")
        if not download_url or not str(download_url).endswith(".json"):
            continue
        payload = fetch_json(download_url)
        if not isinstance(payload, dict):
            continue
        book_name = str(payload.get("book", "")).strip()
        if not book_name:
            continue
        chapters = []
        for raw_chapter in payload.get("chapters", []):
            chapter_number = int(raw_chapter.get("chapter", len(chapters) + 1))
            verses = [
                {
                    "verse": int(raw_verse.get("verse", index + 1)),
                    "text": clean_text(raw_verse.get("text", "")),
                }
                for index, raw_verse in enumerate(raw_chapter.get("verses", []))
            ]
            joined_text = " ".join(verse["text"] for verse in verses)
            chapters.append(
                {
                    "book": book_name,
                    "chapter_number": chapter_number,
                    "chapter_title": f"{book_name} {chapter_number}",
                    "verses": verses,
                    "verse_count": len(verses),
                    "word_count": word_count(joined_text),
                }
            )
        books[book_name] = chapters

    KJV_CACHE_PATH.write_text(json.dumps(books, indent=2, ensure_ascii=False), encoding="utf-8")
    return books


def load_douay_rheims_books() -> dict[str, list[dict[str, Any]]]:
    if DRA_CACHE_PATH.exists():
        return json.loads(DRA_CACHE_PATH.read_text(encoding="utf-8"))

    payload = fetch_json(DRA_URL)
    books: dict[str, list[dict[str, Any]]] = {}
    for book_name, chapter_map in payload.items():
        chapters = []
        for chapter_key in sorted(chapter_map, key=lambda item: int(item)):
            verses_map = chapter_map[chapter_key]
            verses = [
                {
                    "verse": int(verse_key),
                    "text": clean_text(verse_text),
                }
                for verse_key, verse_text in sorted(verses_map.items(), key=lambda item: int(item[0]))
            ]
            joined_text = " ".join(verse["text"] for verse in verses)
            chapter_number = int(chapter_key)
            chapters.append(
                {
                    "book": str(book_name),
                    "chapter_number": chapter_number,
                    "chapter_title": f"{book_name} {chapter_number}",
                    "verses": verses,
                    "verse_count": len(verses),
                    "word_count": word_count(joined_text),
                }
            )
        books[str(book_name)] = chapters

    DRA_CACHE_PATH.write_text(json.dumps(books, indent=2, ensure_ascii=False), encoding="utf-8")
    return books


def gather_track_chapters(books: dict[str, list[dict[str, Any]]], book_names: list[str]) -> list[dict[str, Any]]:
    gathered: list[dict[str, Any]] = []
    for book_name in book_names:
        chapters = books.get(book_name)
        if not chapters:
            raise KeyError(f"Missing book in source data: {book_name}")
        gathered.extend(chapters)
    return gathered


def slice_evenly(items: list[dict[str, Any]], total_days: int) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    total_items = len(items)
    base, remainder = divmod(total_items, total_days)
    cursor = 0
    for index in range(total_days):
        group_size = base + (1 if index < remainder else 0)
        groups.append(items[cursor : cursor + group_size])
        cursor += group_size
    return groups


def compress_references(chapters: list[dict[str, Any]]) -> str:
    if not chapters:
        return "Grace Day"

    grouped: list[tuple[str, list[int]]] = []
    for chapter in chapters:
        book = str(chapter["book"])
        chapter_number = int(chapter["chapter_number"])
        if not grouped or grouped[-1][0] != book:
            grouped.append((book, [chapter_number]))
        else:
            grouped[-1][1].append(chapter_number)

    parts = []
    for book, numbers in grouped:
        ranges = []
        start = prev = numbers[0]
        for current in numbers[1:]:
            if current == prev + 1:
                prev = current
                continue
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = current
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        parts.append(f"{book} {', '.join(ranges)}")
    return " • ".join(parts)


def choose_quote(chapters: list[dict[str, Any]], day_number: int) -> dict[str, str]:
    candidates: list[tuple[int, str, str]] = []
    for chapter in chapters:
        book = str(chapter["book"])
        chapter_number = int(chapter["chapter_number"])
        book_priority = QUOTE_PREFERRED_BOOKS.index(book) if book in QUOTE_PREFERRED_BOOKS else len(QUOTE_PREFERRED_BOOKS)
        for verse in chapter.get("verses", []):
            verse_text = clean_text(verse.get("text", ""))
            if not verse_text:
                continue
            words = word_count(verse_text)
            if 6 <= words <= 28:
                candidates.append(
                    (
                        book_priority,
                        f"{book} {chapter_number}:{int(verse['verse'])}",
                        verse_text,
                    )
                )

    if not candidates and chapters:
        first = chapters[0]
        first_verse = first["verses"][0]
        candidates = [
            (
                0,
                f"{first['book']} {first['chapter_number']}:{first_verse['verse']}",
                clean_text(first_verse["text"]),
            )
        ]

    candidates.sort(key=lambda item: (item[0], len(item[2])))
    reference, text = candidates[0][1], candidates[0][2]
    reflection = REFLECTION_TEMPLATES[(day_number - 1) % len(REFLECTION_TEMPLATES)]
    return {
        "verse": reference,
        "text": text,
        "reflection": reflection,
    }


def build_plan(
    *,
    canon_key: str,
    canon_label: str,
    translation_name: str,
    books: dict[str, list[dict[str, Any]]],
    tracks: dict[str, list[str]],
) -> dict[str, Any]:
    track_groups = [
        slice_evenly(gather_track_chapters(books, track_books), TOTAL_DAYS)
        for track_books in tracks.values()
    ]

    days: list[dict[str, Any]] = []
    for day_index in range(TOTAL_DAYS):
        chapters: list[dict[str, Any]] = []
        for grouped_track in track_groups:
            chapters.extend(grouped_track[day_index])

        references = compress_references(chapters)
        words = sum(int(chapter["word_count"]) for chapter in chapters)
        estimated_minutes = max(5, math.ceil(words / 215))
        quote = choose_quote(chapters, day_index + 1)
        days.append(
            {
                "day_number": day_index + 1,
                "label": f"Day {day_index + 1}",
                "references": references,
                "word_count": words,
                "estimated_minutes": estimated_minutes,
                "translation": translation_name,
                "canon": canon_label,
                "quote": quote,
                "chapters": chapters,
            }
        )

    for index, day in enumerate(days):
        next_day = days[(index + 1) % len(days)]
        day["tomorrow_teaser"] = next_day["references"]

    return {
        "key": canon_key,
        "label": canon_label,
        "translation": translation_name,
        "days": days,
    }


def validate_plan(plan: dict[str, Any]) -> None:
    seen: set[tuple[str, int]] = set()
    for day in plan["days"]:
        for chapter in day["chapters"]:
            verses = chapter.get("verses", [])
            if not verses:
                raise ValueError(f"Empty chapter payload found in {chapter.get('chapter_title')}")
            if int(chapter.get("verse_count", 0)) != len(verses):
                raise ValueError(f"Verse count mismatch in {chapter.get('chapter_title')}")
            key = (str(chapter.get("book")), int(chapter.get("chapter_number", 0)))
            if key in seen:
                raise ValueError(f"Duplicate chapter assigned in plan: {key[0]} {key[1]}")
            seen.add(key)


def build_summary_payload(plans: dict[str, dict[str, Any]]) -> dict[str, Any]:
    today_date = datetime.now(timezone.utc).astimezone().date()
    protestant_day = plans["protestant"]["days"][0]
    catholic_day = plans["catholic"]["days"][0]
    archive_entries = [
        {
            "label": f"Day {entry['day_number']}",
            "day_number": entry["day_number"],
            "references": entry["references"],
            "summary": entry["quote"]["text"],
            "path": f"/bible/?day={entry['day_number']}&canon=protestant",
        }
        for entry in plans["protestant"]["days"]
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "site": {
            "title": SITE_TITLE,
            "short_name": SITE_SHORT_NAME,
            "tagline": TAGLINE,
            "description": SITE_DESCRIPTION,
            "support_url": BUY_ME_A_COFFEE_URL,
            "psalm_91": PSALM_91,
        },
        "canon_choices": CANON_CHOICES,
        "default_profile": {
            "canon": DEFAULT_CANON,
            "start_date": (today_date + timedelta(days=1)).isoformat(),
        },
        "quote_of_day": protestant_day["quote"],
        "encouragement": ENCOURAGEMENT_ITEMS,
        "today": {
            "date": today_date.isoformat(),
            "display_date": today_date.strftime("%A, %B %d, %Y"),
            "day_number": protestant_day["day_number"],
            "references": protestant_day["references"],
            "word_count": protestant_day["word_count"],
            "estimated_minutes": protestant_day["estimated_minutes"],
            "tomorrow_teaser": protestant_day["tomorrow_teaser"],
            "protestant": protestant_day,
            "catholic": catholic_day,
        },
        "progress": {
            "completed_days": 0,
            "percentage": 0,
            "calendar_month": today_date.strftime("%B %Y"),
            "calendar_days": build_placeholder_calendar(today_date),
            "catch_up": [
                "Missed days stay visible, but gently. Catch-up should feel like an invitation, not a scolding.",
                "Leap years can be treated as grace days or review days without breaking the plan.",
                "Marking a day complete should never block today's reading from staying open on the page.",
            ],
        },
        "archive": archive_entries,
        "plans": {
            canon_key: {
                "label": plan["label"],
                "translation": plan["translation"],
                "total_days": TOTAL_DAYS,
                "days": [
                    {
                        "day_number": day["day_number"],
                        "references": day["references"],
                        "word_count": day["word_count"],
                        "estimated_minutes": day["estimated_minutes"],
                        "quote": day["quote"],
                        "tomorrow_teaser": day["tomorrow_teaser"],
                    }
                    for day in plan["days"]
                ],
            }
            for canon_key, plan in plans.items()
        },
        "settings": {
            "email_frequency": "One daily email with that day’s complete chapters.",
            "install_label": "Install the PWA to keep today’s reading available offline.",
        },
    }


def build_placeholder_calendar(today: date) -> list[dict[str, Any]]:
    first_day = today.replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1, day=1)
    total_days = (next_month - first_day).days
    output = []
    for offset in range(total_days):
        current = first_day + timedelta(days=offset)
        output.append(
            {
                "day": current.day,
                "status": "today" if current == today else ("future" if current > today else "read"),
                "label": current.isoformat(),
            }
        )
    return output


def write_day_payloads(plans: dict[str, dict[str, Any]]) -> None:
    for canon_key, plan in plans.items():
        canon_dir = READINGS_DIR / canon_key
        canon_dir.mkdir(parents=True, exist_ok=True)
        for day in plan["days"]:
            path = canon_dir / f"day-{day['day_number']:03d}.json"
            path.write_text(
                json.dumps(
                    {
                        "day_number": day["day_number"],
                        "references": day["references"],
                        "word_count": day["word_count"],
                        "estimated_minutes": day["estimated_minutes"],
                        "translation": day["translation"],
                        "canon": day["canon"],
                        "quote": day["quote"],
                        "tomorrow_teaser": day["tomorrow_teaser"],
                        "chapters": day["chapters"],
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )


def page_shell(*, title: str, description: str, canonical_path: str, body_class: str, content: str) -> str:
    canonical_url = f"{BASE_URL}{canonical_path}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta name="theme-color" content="{THEME_COLOR}">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="{BRAND_NAME}">
  <link rel="canonical" href="{canonical_url}">
  <link rel="manifest" href="/manifest.webmanifest">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{escape(BRAND_NAME)}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{BASE_URL}{asset_url(BRAND_OG_IMAGE)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(description)}">
  <meta name="twitter:image" content="{BASE_URL}{asset_url(BRAND_OG_IMAGE)}">
  <meta name="twitter:site" content="{FOUNDER_X_HANDLE}">
  <meta name="keywords" content="AI engineering, iOS engineering, Web engineering, LLM integration, RAG pipelines, Shadowfetch">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="icon" href="{asset_url('shadowfetch-mark.svg')}" type="image/svg+xml">
  <link rel="stylesheet" href="{asset_url('styles.css')}">
</head>
<body data-edition="studio" data-page="{escape(body_class)}">
  {render_header()}
  <main>{content}</main>
  {render_footer()}
  <script src="{asset_url('app.js')}"></script>
</body>
</html>
"""


def render_header() -> str:
    return f"""
  <header class="site-header">
    <div class="header-utility">
      <div class="container utility-row">
        <p class="utility-copy">Precision. Reliability. Architectural Excellence.</p>
        <div class="utility-social">
          <a href="{FOUNDER_X_URL}" target="_blank" rel="noreferrer noopener">Founder {FOUNDER_X_HANDLE}</a>
          <a href="{CEO_X_URL}" target="_blank" rel="noreferrer noopener">CEO {CEO_X_HANDLE}</a>
        </div>
      </div>
    </div>
    <div class="container header-row">
      <a class="brand-lockup" href="/" aria-label="{BRAND_NAME} home">
        <span class="brand-mark" aria-hidden="true">SF</span>
        <span class="brand-copy">
          <strong>{BRAND_NAME}</strong>
          <small>{BRAND_DIVISION}</small>
        </span>
      </a>
      <nav class="site-nav" aria-label="Primary">
        <a href="/#services">Services</a>
        <a href="/#standards">Standards</a>
        <a href="/#perspective">Whitepapers</a>
        <a href="/#contact">Contact</a>
      </nav>
      <div class="header-actions">
        <a class="header-link" href="{BUY_ME_A_COFFEE_URL}" target="_blank" rel="noreferrer noopener">Buy Me a Coffee</a>
        <a class="button button-secondary button-compact" href="/signup/">Start an Engagement</a>
      </div>
    </div>
  </header>
"""


def render_footer() -> str:
    return f"""
  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <p class="footer-title">{BRAND_NAME}</p>
        <p class="footer-copy">{BRAND_DESCRIPTION}</p>
        <p class="footer-note">The outbound mail stack remains in place for future Shadowfetch briefings and newsletters.</p>
      </div>
      <div class="footer-links">
        <a href="{mailto_url('Shadowfetch engineering inquiry', FOOTER_INQUIRY_BODY)}" data-copy-email="{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
        <a href="{FOUNDER_X_URL}" target="_blank" rel="noreferrer noopener">Founder {FOUNDER_X_HANDLE}</a>
        <a href="{CEO_X_URL}" target="_blank" rel="noreferrer noopener">CEO {CEO_X_HANDLE}</a>
        <a href="{BUY_ME_A_COFFEE_URL}" target="_blank" rel="noreferrer noopener">Buy Me a Coffee</a>
      </div>
      <div class="footer-meta">
        <span class="footer-stat footer-stat-counter"><span>Total Visitors</span><strong data-visit-count>—</strong></span>
        <span class="footer-stat"><span>Mail Infrastructure</span><strong>Preserved</strong></span>
        <span class="footer-stat"><span>Copyright</span><strong>© <span data-current-year></span> {BRAND_NAME}</strong></span>
      </div>
    </div>
  </footer>
"""


def escape(value: Any) -> str:
    return html.escape(str(value or ""))


def render_signup_form(form_id: str, compact: bool = False) -> str:
    card_class = "signup-card signup-card-compact" if compact else "signup-card"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return f"""
      <form class="{card_class}" id="{form_id}" data-signup-form>
        <p class="panel-label">Daily Bible email</p>
        <h3>Enter your email and subscribe.</h3>
        <label class="field-label">Email address
          <input class="text-input" type="email" name="email" placeholder="you@example.com" required>
        </label>
        <input type="hidden" name="canon" value="protestant">
        <input type="hidden" name="start_date" value="{tomorrow}">
        <div class="form-actions">
          <button class="button button-primary" type="submit">Subscribe</button>
        </div>
        <p class="form-note" data-signup-status>Your first reading arrives tomorrow. No account. No paywall. Complete chapters only.</p>
      </form>
    """


def render_platform_band() -> str:
    items = [
        "Swift",
        "iOS",
        "React",
        "Next.js",
        "TypeScript",
        "OpenAI",
        "Anthropic",
        "Cloudflare",
        "Edge Runtime",
        "CI/CD",
    ]
    item_markup = "".join(f"<span>{escape(item)}</span>" for item in items)
    return f"""
      <section class="platform-band" aria-label="Technology alignment">
        <div class="container platform-band-row">
          <p>Built across the stacks modern product teams operate on.</p>
          <div class="platform-ticker">
            {item_markup}
          </div>
        </div>
      </section>
    """


def render_leadership_feed() -> str:
    profiles = [
        ("MrBobCorbin", "Robert Corbin", "Founder"),
        ("Kaitlancorbin1", "Kaitlan Corbin", "CEO"),
    ]
    button_markup = "".join(
        f'<button class="x-feed-toggle{" is-active" if index == 0 else ""}" type="button" data-x-toggle="{handle}" aria-pressed="{"true" if index == 0 else "false"}">{escape(label)} <span>{escape(role)}</span></button>'
        for index, (handle, label, role) in enumerate(profiles)
    )
    panel_markup = "".join(
        f"""
          <article class="x-feed-panel{" is-active" if index == 0 else ""}" data-x-panel data-x-handle="{handle}">
            <div class="x-feed-cardhead">
              <div>
                <p class="section-kicker">{escape(role)}</p>
                <h3>{escape(label)}</h3>
              </div>
              <a class="text-link" href="https://x.com/{handle}" target="_blank" rel="noreferrer noopener">@{handle}</a>
            </div>
            <div class="x-feed-embed" data-x-embed data-screen-name="{handle}" data-profile-label="{escape(label)}">
              <p class="x-feed-loading">Loading the latest post from @{escape(handle)}.</p>
            </div>
          </article>
        """
        for index, (handle, label, role) in enumerate(profiles)
    )
    return f"""
      <section class="leadership-feed-shell">
        <div class="container leadership-feed-layout" data-x-rotator data-x-interval="12000">
          <div class="leadership-feed-copy" data-reveal>
            <p class="eyebrow">Leadership Feed</p>
            <h2>Latest signals from the people building Shadowfetch.</h2>
            <p class="section-copy">This module alternates between the most recent post from Robert and Kaitlan using X’s official embedded timeline format. It refreshes with the page and rotates between both leadership accounts automatically.</p>
            <div class="x-feed-toggle-row" role="tablist" aria-label="Leadership X feeds">
              {button_markup}
            </div>
          </div>
          <div class="x-feed-stage" data-reveal>
            {panel_markup}
          </div>
        </div>
      </section>
    """


def render_services_grid() -> str:
    cards = [
        (
            "Intelligent Systems",
            "Custom LLM integration and RAG pipelines for proprietary data.",
            "Retrieval, evaluation, governance, and deployment designed for teams that need answers grounded in their own systems.",
        ),
        (
            "High-Performance Mobile",
            "Native iOS development tuned for low-latency interaction and fluid UI.",
            "Swift systems architecture, performance-sensitive interfaces, and product execution that stays close to the hardware.",
        ),
        (
            "Scalable Web Infrastructure",
            "Enterprise-grade React and Next.js architectures built for reliability.",
            "Operationally disciplined frontends, edge-aware delivery, and maintainable systems designed to last beyond launch week.",
        ),
    ]
    card_markup = "".join(
        f"""
          <article class="service-card" data-reveal>
            <p class="section-kicker">{escape(title)}</p>
            <h3>{escape(summary)}</h3>
            <p>{escape(body)}</p>
          </article>
        """
        for title, summary, body in cards
    )
    return f"""
      <section class="section-shell" id="services">
        <div class="container">
          <div class="section-heading" data-reveal>
            <div>
              <p class="eyebrow">Core Pillars</p>
              <h2>Strategic services designed for business-critical delivery.</h2>
            </div>
            <p class="section-copy">Shadowfetch is positioned for organizations that value disciplined execution over demo-driven theatrics.</p>
          </div>
          <div class="service-grid">
            {card_markup}
          </div>
        </div>
      </section>
    """


def render_standards_section() -> str:
    proof_cards = [
        (
            "Security First",
            "SOC2-aligned delivery workflows, isolated secrets handling, and review discipline suitable for regulated environments.",
        ),
        (
            "Edge-Native",
            "Global delivery strategies designed to push critical interactions toward sub-50ms targets where topology allows.",
        ),
        (
            "AI Integration",
            "Beyond wrappers: retrieval, evaluation, and domain-specific model behavior tuned to operational reality.",
        ),
        (
            "Code Integrity",
            "Strict TypeScript and Swift, automated CI gates, and systems built to remain understandable under pressure.",
        ),
    ]
    proof_markup = "".join(
        f"""
          <article class="proof-card" data-reveal>
            <p class="section-kicker">{escape(title)}</p>
            <p>{escape(body)}</p>
          </article>
        """
        for title, body in proof_cards
    )
    return f"""
      <section class="section-shell section-shell-contrast" id="standards">
        <div class="container standards-layout">
          <div class="standards-copy" data-reveal>
            <p class="eyebrow">Elite Engineering</p>
            <h2>Delivery standards that make technical risk visible before it becomes operational debt.</h2>
            <p class="section-copy">The objective is not novelty. The objective is dependable systems architecture, measurable quality gates, and a product surface that feels inevitable to the end user.</p>
            <div class="process-steps">
              <article>
                <span>01</span>
                <h3>Diagnose</h3>
                <p>Clarify the system constraints, latency budgets, data boundaries, and decision loops that matter.</p>
              </article>
              <article>
                <span>02</span>
                <h3>Architect</h3>
                <p>Design the application surface, data model, and AI orchestration around long-term maintainability.</p>
              </article>
              <article>
                <span>03</span>
                <h3>Deploy</h3>
                <p>Ship with testing discipline, instrumentation, and a delivery model intended for production, not theater.</p>
              </article>
            </div>
          </div>
          <div class="proof-grid">
            {proof_markup}
          </div>
        </div>
      </section>
    """


def render_perspective_section() -> str:
    whitepapers = [
        (
            "AI Safety by Construction",
            "Guardrails, evaluation loops, and retrieval boundaries for systems that have to survive real-world use.",
        ),
        (
            "Private Data Architectures",
            "RAG systems and integration patterns that preserve privacy, traceability, and executive confidence.",
        ),
        (
            "Modular Delivery Systems",
            "Codebase structures that keep web, mobile, and AI surfaces coherent as teams and product scope expand.",
        ),
    ]
    paper_markup = "".join(
        f"""
          <article class="paper-card" data-reveal>
            <p class="section-kicker">Technical Whitepaper</p>
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
            <a class="text-link" href="{mailto_url(f'Request: {title}', f'I would like the Shadowfetch whitepaper: {title}.')}">Request the briefing</a>
          </article>
        """
        for title, body in whitepapers
    )
    return f"""
      <section class="section-shell" id="perspective">
        <div class="container">
          <div class="section-heading" data-reveal>
            <div>
              <p class="eyebrow">Perspective</p>
              <h2>Thought leadership for teams selecting an engineering partner, not a feature factory.</h2>
            </div>
            <p class="section-copy">Shadowfetch publishes its operating logic directly: safety, privacy, modularity, and the architectural tradeoffs behind AI-native products.</p>
          </div>
          <div class="paper-grid">
            {paper_markup}
          </div>
        </div>
      </section>
    """


def render_contact_section() -> str:
    return f"""
      <section class="section-shell section-shell-final" id="contact">
        <div class="container contact-layout">
          <article class="contact-card contact-card-primary" data-reveal>
            <p class="eyebrow">Start the Conversation</p>
            <h2>For CTOs, product leaders, and operators building serious software.</h2>
            <p>Send the operating context, technical constraints, and what must not fail. Shadowfetch will respond with a direct engineering path, not a general pitch deck.</p>
            <div class="hero-actions">
              <a class="button button-primary" href="{mailto_url('Shadowfetch engineering inquiry', GENERAL_INQUIRY_BODY)}">Email Shadowfetch</a>
              <a class="button button-secondary" href="/signup/">Engagement page</a>
            </div>
          </article>
          <article class="contact-card" data-reveal>
            <p class="section-kicker">Direct Channels</p>
            <div class="contact-list">
              <a href="{FOUNDER_X_URL}" target="_blank" rel="noreferrer noopener">Founder on X <strong>{FOUNDER_X_HANDLE}</strong></a>
              <a href="{CEO_X_URL}" target="_blank" rel="noreferrer noopener">CEO on X <strong>{CEO_X_HANDLE}</strong></a>
              <a href="{mailto_url('Shadowfetch engineering inquiry')}" data-copy-email="{CONTACT_EMAIL}">Email <strong>{CONTACT_EMAIL}</strong></a>
            </div>
            <p class="contact-note">Mail infrastructure remains active for a future Shadowfetch briefing newsletter. It is preserved, but intentionally not the primary call to action.</p>
          </article>
        </div>
      </section>
    """


def render_chapter_block(chapter: dict[str, Any]) -> str:
    verse_rows = "".join(
        f'<p class="verse-row"><span class="verse-number">{verse["verse"]}</span><span>{escape(verse["text"])}</span></p>'
        for verse in chapter.get("verses", [])
    )
    return f"""
      <article class="panel chapter-reading">
        <p class="panel-label">Chapter</p>
        <h3>{escape(chapter.get("chapter_title"))}</h3>
        <div class="reading-meta">
          <span>{chapter.get("verse_count", 0)} verses</span>
          <span>{chapter.get("word_count", 0)} words</span>
        </div>
        <div class="verse-stack">
          {verse_rows}
        </div>
      </article>
    """


def render_day_article(day: dict[str, Any], *, show_quote: bool = False) -> str:
    chapters_markup = "".join(render_chapter_block(chapter) for chapter in day.get("chapters", []))
    quote_markup = ""
    if show_quote:
        quote = day["quote"]
        quote_markup = f"""
          <article class="panel quote-panel">
            <p class="panel-label">Verse of the day</p>
            <blockquote class="quote-block">
              <p>{escape(quote['text'])}</p>
              <footer>{escape(quote['verse'])}</footer>
            </blockquote>
            <p>{escape(quote['reflection'])}</p>
          </article>
        """
    return f"""
      <div class="reading-lead-body">
        <p class="paper-kicker">Today's Reading</p>
        <h1 class="paper-headline bible-headline">Day {day['day_number']}</h1>
        <p class="paper-summary">{escape(day['references'])}</p>
        <div class="reading-meta reading-meta-strong">
          <span>{day['estimated_minutes']} minute read</span>
          <span>{day['word_count']} words</span>
          <span>{escape(day['translation'])}</span>
        </div>
        <div class="reading-stack">{chapters_markup}</div>
        <div class="hero-actions devotional-actions">
          <a class="button button-primary" href="/signup/">Get the daily email</a>
        </div>
        <p class="tomorrow-teaser">Tomorrow&apos;s teaser: {escape(day['tomorrow_teaser'])}</p>
        {quote_markup}
      </div>
    """


def render_home_preview(day: dict[str, Any]) -> str:
    return f"""
      <div class="reading-lead-body reading-preview">
        <p class="paper-kicker">Today's Reading</p>
        <h1 class="paper-headline bible-headline">Day {day['day_number']}</h1>
        <p class="paper-summary">{escape(day['references'])}</p>
        <div class="reading-meta reading-meta-strong">
          <span>{day['estimated_minutes']} minute read</span>
          <span>{day['word_count']} words</span>
          <span>{escape(day['translation'])}</span>
        </div>
        <p class="reading-preview-copy">A calm 365-day Bible reading delivered one day at a time. Every email includes complete chapters only.</p>
        <div class="hero-actions devotional-actions reading-preview-actions">
          <a class="button button-primary" href="/signup/">Subscribe</a>
        </div>
        <p class="form-note reading-preview-note">Choose your canon, pick a start date, and the email begins from your day in the plan.</p>
      </div>
    """


def render_home_page(payload: dict[str, Any]) -> str:
    hero = f"""
      {render_leadership_feed()}
      <section class="hero-shell">
        <div class="container hero-layout">
          <div class="hero-copy" data-reveal>
            <p class="eyebrow">The Standard of Engineering</p>
            <h1>Engineering the Next Generation of Intelligence.</h1>
            <p class="hero-text">{BRAND_DESCRIPTION}</p>
            <p class="hero-support">Shadowfetch is engineered for operators who care about durable systems, direct communication, and AI-native product architecture that can withstand production pressure.</p>
            <div class="hero-actions">
              <a class="button button-primary" href="/signup/">Start an Engagement</a>
              <a class="button button-secondary" href="/#standards">Review Delivery Standards</a>
            </div>
            <dl class="hero-metrics">
              <div>
                <dt>Focus</dt>
                <dd>Mission-critical web and iOS systems.</dd>
              </div>
              <div>
                <dt>Operating Style</dt>
                <dd>Direct, economical, architecture-first execution.</dd>
              </div>
              <div>
                <dt>AI Position</dt>
                <dd>Structured systems, not thin wrappers.</dd>
              </div>
            </dl>
          </div>
          <div class="hero-visual" data-reveal>
            <div class="architectural-frame">
              <div class="frame-ornament frame-ornament-top"></div>
              <div class="frame-ornament frame-ornament-bottom"></div>
              <article class="crest-card">
                <p class="section-kicker">Heritage Mark</p>
                <img src="{asset_url(BRAND_OG_IMAGE)}" alt="Shadowfetch crest logo with a hound and the words iOS and Web Applications">
                <p>The original crest remains, reframed inside a stricter operating system.</p>
              </article>
              <div class="floating-badge floating-badge-primary">AI-native architecture</div>
              <div class="floating-badge floating-badge-secondary">Edge-ready delivery</div>
            </div>
          </div>
        </div>
      </section>
      {render_platform_band()}
      {render_services_grid()}
      {render_standards_section()}
      {render_perspective_section()}
      {render_contact_section()}
    """

    return page_shell(
        title=f"{BRAND_NAME} | {BRAND_DIVISION}",
        description=BRAND_DESCRIPTION,
        canonical_path="/",
        body_class="home",
        content=hero,
    )


def render_bible_page(payload: dict[str, Any]) -> str:
    content = f"""
      <section class="subpage-shell">
        <div class="container subpage-hero" data-reveal>
          <p class="eyebrow">Technical Standards</p>
          <h1>Architecture decisions should survive contact with scale, regulation, and latency.</h1>
          <p class="section-copy">Shadowfetch treats web, mobile, and AI architecture as one operating problem. These are the standards behind that approach.</p>
        </div>
      </section>
      {render_standards_section()}
      {render_perspective_section()}
    """
    return page_shell(
        title=f"Technical Standards | {BRAND_NAME}",
        description="Shadowfetch delivery standards for AI systems, web infrastructure, mobile performance, and engineering governance.",
        canonical_path="/bible/",
        body_class="bible",
        content=content,
    )


def render_retired_page(label: str, path: str) -> str:
    content = f"""
      <section class="subpage-shell">
        <article class="container simple-panel" data-reveal>
          <p class="eyebrow">{escape(label)}</p>
          <h1>This section has been consolidated into the main Shadowfetch site.</h1>
          <p class="hero-text">The current brand architecture is intentionally tighter: clear positioning, direct service lines, and a single primary route into engagement.</p>
          <div class="hero-actions">
            <a class="button button-primary" href="/">Return home</a>
          </div>
        </article>
      </section>
    """
    return page_shell(
        title=f"{label} | {BRAND_NAME}",
        description="This section has been folded into the current Shadowfetch consulting site.",
        canonical_path=path,
        body_class=label.lower().replace(" ", "-"),
        content=content,
    )


def render_settings_page(payload: dict[str, Any]) -> str:
    content = f"""
      <section class="subpage-shell">
        <div class="container content-grid content-grid-tight">
          <article class="content-card" data-reveal>
            <p class="eyebrow">Briefings</p>
            <h1>Mail infrastructure remains available for future Shadowfetch dispatches.</h1>
            <p>The existing outbound email stack has been preserved so Shadowfetch can introduce a future newsletter or executive briefing without rebuilding delivery from zero.</p>
          </article>
          <article class="content-card" data-reveal>
            <p class="section-kicker">Current posture</p>
            <h3>Direct contact first.</h3>
            <p>For now, engagement begins through direct conversation instead of list-driven capture. That keeps the operating signal high while the brand architecture tightens.</p>
            <a class="text-link" href="{mailto_url('Shadowfetch briefing inquiry')}">Discuss future briefings</a>
          </article>
        </div>
      </section>
    """
    return page_shell(
        title=f"Briefings | {BRAND_NAME}",
        description="Shadowfetch keeps its email infrastructure in reserve for future newsletters and technical briefings.",
        canonical_path="/settings/",
        body_class="settings",
        content=content,
    )


def render_signup_page(payload: dict[str, Any]) -> str:
    content = f"""
      <section class="subpage-shell">
        <div class="container content-grid">
          <article class="content-card content-card-primary" data-reveal>
            <p class="eyebrow">Start an Engagement</p>
            <h1>Bring the system constraints, the product ambition, and the deadlines that actually matter.</h1>
            <p>Shadowfetch is built for organizations that need senior engineering judgment across AI integration, native iOS execution, and resilient web architecture.</p>
            <div class="hero-actions">
              <a class="button button-primary" href="{mailto_url('Shadowfetch engineering inquiry', ENGAGEMENT_INQUIRY_BODY)}">Email project details</a>
              <a class="button button-secondary" href="{FOUNDER_X_URL}" target="_blank" rel="noreferrer noopener">Message the founder on X</a>
            </div>
          </article>
          <article class="content-card" data-reveal>
            <p class="section-kicker">What to send</p>
            <div class="detail-stack">
              <article>
                <h3>Business context</h3>
                <p>What the application must change for the organization, and what failure would cost.</p>
              </article>
              <article>
                <h3>System constraints</h3>
                <p>Current stack, privacy expectations, latency budgets, and non-negotiable dependencies.</p>
              </article>
              <article>
                <h3>Decision window</h3>
                <p>Desired launch timing, stakeholder ownership, and whether the need is diagnostic, architectural, or delivery-oriented.</p>
              </article>
            </div>
          </article>
          <article class="content-card" data-reveal>
            <p class="section-kicker">Leadership Channels</p>
            <div class="contact-list">
              <a href="{FOUNDER_X_URL}" target="_blank" rel="noreferrer noopener">Founder on X <strong>{FOUNDER_X_HANDLE}</strong></a>
              <a href="{CEO_X_URL}" target="_blank" rel="noreferrer noopener">CEO on X <strong>{CEO_X_HANDLE}</strong></a>
              <a href="{mailto_url('Shadowfetch engineering inquiry')}" data-copy-email="{CONTACT_EMAIL}">Email <strong>{CONTACT_EMAIL}</strong></a>
            </div>
          </article>
        </div>
      </section>
    """
    return page_shell(
        title=f"Start an Engagement | {BRAND_NAME}",
        description="Contact Shadowfetch for AI engineering, native iOS delivery, and enterprise-grade web architecture.",
        canonical_path="/signup/",
        body_class="signup",
        content=content,
    )


def render_thanks_page() -> str:
    content = f"""
      <section class="subpage-shell">
        <article class="container simple-panel" data-reveal>
          <p class="eyebrow">Message Received</p>
          <h1>Shadowfetch has the brief.</h1>
          <p class="hero-text">The next step is a direct conversation about scope, constraints, and the engineering path that makes sense.</p>
          <div class="hero-actions">
            <a class="button button-primary" href="/">Return home</a>
          </div>
        </article>
      </section>
    """
    return page_shell(
        title=f"Received | {BRAND_NAME}",
        description="Shadowfetch has received the inquiry and will continue the conversation directly.",
        canonical_path="/blessed/",
        body_class="thanks",
        content=content,
    )


def build_manifest() -> str:
    return json.dumps(
        {
            "name": BRAND_NAME,
            "short_name": BRAND_NAME,
            "start_url": "/",
            "display": "standalone",
            "background_color": THEME_COLOR,
            "theme_color": THEME_COLOR,
            "description": BRAND_DESCRIPTION,
            "icons": [
                {
                    "src": "/assets/shadowfetch-mark.svg",
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any",
                }
            ],
        },
        indent=2,
    )


def build_service_worker() -> str:
    return """const CACHE_NAME = "shadowfetch-studio-v1";
const CORE_ASSETS = [
  "/manifest.webmanifest",
  "/assets/styles.css",
  "/assets/app.js",
  "/assets/shadowfetch-mark.svg",
  "/assets/shadowfetch-crest.jpg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }
  const url = new URL(event.request.url);
  const isSameOrigin = url.origin === self.location.origin;
  const isDocument = event.request.mode === "navigate" || event.request.destination === "document";

  if (isSameOrigin && isDocument) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then((response) => {
        if (response.ok && event.request.url.startsWith(self.location.origin)) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const clone = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    throw new Error("Network unavailable and no cached document found.");
  }
}
"""


if __name__ == "__main__":
    main()
