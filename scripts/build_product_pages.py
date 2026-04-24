#!/usr/bin/env python3

from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://www.shadowfetch.com"


PRODUCTS = [
    {
        "slug": "fast-pdf",
        "title": "Fast PDF",
        "theme": "theme-fast-pdf",
        "category": "Capture Utility",
        "tagline": "Take a page. Save a PDF. Stay in the camera.",
        "summary": "Fast PDF is a speed-first document app for iPhone and iPad. It keeps the capture loop short, turns each shot into its own PDF, and writes straight into Files so the user can move through real paper without the usual scanning drag.",
        "icon": "/fast-pdf/assets/icon-1024.png",
        "hero_image": "/fast-pdf/assets/home.png",
        "hero_alt": "Fast PDF home screen preview",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "Files or iCloud Drive"),
            ("Account", "None"),
            ("Best use", "Rapid page capture"),
        ],
        "details_intro": "The point of Fast PDF is speed under real use. It is meant for stacks of forms, receipts, and loose paper where every extra tap slows the user down.",
        "details": [
            ("What it is", "A live capture loop for PDFs", "The app keeps the camera active, saves each page immediately, and lets the user keep moving instead of pausing after every shot."),
            ("Why it matters", "Scanning should not feel ceremonial", "Most scanning apps add too much review friction. Fast PDF exists to make single-page PDF output feel immediate and practical."),
            ("Where it fits", "Operational paperwork and daily admin", "It works best for people who create many small PDFs and care more about speed and clean export than archival workflows."),
        ],
        "gallery": [
            ("/fast-pdf/assets/home.png", "Fast PDF home screen", "The main capture surface is kept minimal so the user can start scanning immediately."),
            ("/fast-pdf/assets/rapid-camera.png", "Fast PDF rapid camera mode", "Rapid mode keeps the camera hot between saves so repeated page capture stays fast."),
            ("/fast-pdf/assets/saved-run-ipad.png", "Fast PDF saved files on iPad", "The saved-run view shows the resulting PDFs without making the user leave the app flow."),
        ],
        "links": [
            ("Support", "/fast-pdf/support/"),
            ("Privacy", "/fast-pdf/privacy/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Fast PDF is the narrowest kind of utility on purpose: fast in, clean PDF out, and no cloud account in the middle.",
    },
    {
        "slug": "grandmas-cookbook",
        "title": "Grandma's Cookbook",
        "theme": "theme-grandmas-cookbook",
        "category": "Family Archive",
        "tagline": "Save the cookbook before the handwriting fades.",
        "summary": "Grandma's Cookbook turns old recipe binders, handwritten cards, and kitchen notebooks into a searchable family archive. It builds long PDFs, preserves page images, and lets the user repair OCR mistakes where flour, fading ink, and margin notes confuse the scanner.",
        "icon": "/grandmas-cookbook/assets/icon-1024.png",
        "hero_image": "/grandmas-cookbook/assets/home-hero.jpg",
        "hero_alt": "Grandma's Cookbook home screen preview",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "On device"),
            ("OCR", "Built in and editable"),
            ("Best use", "Family recipe preservation"),
        ],
        "details_intro": "This app is not just a scanner. It is a preservation tool for recipe history, with room for corrections, family context, and long-form archive behavior.",
        "details": [
            ("What it is", "A recipe archive builder", "Each cookbook becomes one real volume with page images, searchable text, and a long PDF instead of a scattered photo roll."),
            ("Why it matters", "Family history is fragile", "Old recipes often live in notebooks and binders that are damaged, unique, and hard to search. The app exists to make that material durable and usable."),
            ("Where it fits", "Heirloom archiving and family memory", "It is best for people preserving recipe books they do not want to lose, not for disposable weeknight meal planning."),
        ],
        "gallery": [
            ("/grandmas-cookbook/assets/home-hero.jpg", "Grandma's Cookbook home shelf", "The shelf view presents each family volume like a keepsake collection instead of a file list."),
            ("/grandmas-cookbook/assets/archive-detail.jpg", "Grandma's Cookbook archive detail", "Saved volumes keep context, pages, and narrative together so the cookbook feels like history, not just OCR text."),
            ("/grandmas-cookbook/assets/page-editor.jpg", "Grandma's Cookbook page editor", "The editor is there because recipe OCR will miss scribbles, stains, and handwritten abbreviations."),
        ],
        "links": [
            ("Support", "/grandmas-cookbook/support/"),
            ("Privacy", "/grandmas-cookbook/privacy/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Grandma's Cookbook is meant to preserve family material without flattening it into generic scan output.",
    },
    {
        "slug": "hush",
        "title": "Hush",
        "theme": "theme-hush",
        "category": "Privacy Utility",
        "tagline": "Encrypt locally. Paste anywhere.",
        "summary": "Hush is a local-first text encryption tool for iPhone and iPad. It protects message text on device with a shared secret, then lets the user paste the encrypted output into any app they already use instead of asking them to join a new messaging network.",
        "icon": "/assets/portfolio/hush-icon.png",
        "hero_image": "/assets/portfolio/hush-icon.png",
        "hero_alt": "Hush app icon",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "On device"),
            ("Network", "Not required"),
            ("Best use", "Private text preparation"),
        ],
        "details_intro": "Hush stays small on purpose. The app is useful because it does one job clearly: protect the text first, then get out of the way.",
        "details": [
            ("What it is", "A local encryption layer for text", "The user writes plain text, applies a shared secret, and copies the encrypted result into Messages, Mail, or any other app."),
            ("Why it matters", "Not every privacy tool needs its own network", "Many people want to protect text without adopting a new platform, account, or inbox. Hush exists for that narrower need."),
            ("Where it fits", "Private handoff before delivery", "It works best where the person already has a communication channel and only needs a safer way to prepare the message content."),
        ],
        "gallery": [],
        "links": [
            ("Support", "/hush/support/"),
            ("Privacy", "/hush/privacy/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Hush is deliberately not a chat platform. It is a privacy utility that secures text before the user leaves the app.",
    },
    {
        "slug": "receipt-to-pdf",
        "title": "Receipt to PDF",
        "theme": "theme-receipt-to-pdf",
        "category": "Document Utility",
        "tagline": "Turn receipts into clean PDFs without a whole expense stack.",
        "summary": "Receipt to PDF is a local-first receipt scanner for iPhone and iPad. It uses VisionKit capture, exports clean PDFs, supports Files integration, and keeps the workflow lightweight for people who want documentation without adopting a full expense platform.",
        "icon": "/assets/portfolio/receipt-to-pdf-icon.png",
        "hero_image": "/receipt-to-pdf/assets/home.png",
        "hero_alt": "Receipt to PDF home screen preview",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "Files and local"),
            ("Protection", "Optional local passcode"),
            ("Best use", "Receipts and proof-of-purchase"),
        ],
        "details_intro": "The app exists for a common operational problem: people need clean receipts in PDF form, but they do not want a bloated bookkeeping system around it.",
        "details": [
            ("What it is", "A receipt-specific PDF tool", "The camera flow is tailored toward short paper documents, and export stays close to Apple’s native Files model."),
            ("Why it matters", "Receipts disappear into camera rolls fast", "This app gives them a better destination and format before they get lost or become annoying to retrieve later."),
            ("Where it fits", "Reimbursements, taxes, and records", "It is useful for freelancers, small operators, and anyone who needs simple receipt retention without a SaaS subscription."),
        ],
        "gallery": [
            ("/receipt-to-pdf/assets/home.png", "Receipt to PDF home screen", "The home screen keeps the capture and export choices straightforward."),
            ("/receipt-to-pdf/assets/draft.png", "Receipt to PDF draft preview", "The draft preview helps the user catch bad edges before they save the final PDF."),
            ("/receipt-to-pdf/assets/ipad-export.png", "Receipt to PDF iPad export screen", "Export stays aligned to Files and common Apple sharing patterns instead of a proprietary inbox."),
        ],
        "links": [
            ("Support", "/receipt-to-pdf/support/"),
            ("Privacy", "/receipt-to-pdf/privacy/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Receipt to PDF is built for clean recordkeeping, not for trapping the user inside another expense service.",
    },
    {
        "slug": "renew-guard",
        "title": "Renew Guard",
        "theme": "theme-renew-guard",
        "category": "Tracking Utility",
        "tagline": "Stop getting surprised by subscription renewals.",
        "summary": "Renew Guard is a local-first subscription tracker for iPhone and iPad. It helps the user record recurring bills, spot upcoming charges, and act before renewal day instead of realizing too late that another service rolled over.",
        "icon": "/assets/portfolio/renew-guard-icon.png",
        "hero_image": "/assets/portfolio/renew-guard-icon.png",
        "hero_alt": "Renew Guard app icon",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "Local"),
            ("Input", "Manual entry and OCR assist"),
            ("Best use", "Renewal oversight"),
        ],
        "details_intro": "Renew Guard is about control. The user should be able to see recurring commitments clearly and decide early instead of reacting after the charge already posted.",
        "details": [
            ("What it is", "A renewal visibility tool", "It records subscriptions, tracks renewal dates, and surfaces the countdown in a cleaner, more deliberate way than digging through email."),
            ("Why it matters", "Recurring charges hide in plain sight", "Most people remember subscriptions only when they are billed. Renew Guard exists to move that awareness forward."),
            ("Where it fits", "Personal finance and admin cleanup", "It is useful for anyone carrying multiple software, media, or utility subscriptions who wants a better pre-billing review habit."),
        ],
        "gallery": [],
        "links": [
            ("Support", "/renew-guard/support/"),
            ("Privacy", "/renew-guard/privacy/"),
            ("Accessibility", "/renew-guard/accessibility/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Renew Guard works best as a quiet control surface for recurring bills, not as a noisy finance dashboard.",
    },
    {
        "slug": "shift-swap-liaison",
        "title": "Shift Swap Liaison",
        "theme": "theme-shift-swap-liaison",
        "category": "Workforce Utility",
        "tagline": "Fast team shift handoffs without a backend-heavy stack.",
        "summary": "Shift Swap Liaison turns a messy shift handoff into a direct mobile workflow. One person creates the shift, another claims it through the app, and the acceptance is pushed back into manager-ready communication without requiring a full scheduling platform.",
        "icon": "/shift-swap-liaison/assets/icon-1024.png",
        "hero_image": "/shift-swap-liaison/assets/create.png",
        "hero_alt": "Shift Swap Liaison create screen",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Backend", "Not required"),
            ("Share path", "QR and deep link"),
            ("Best use", "Shift handoff coordination"),
        ],
        "details_intro": "The product is meant to solve one operational problem well: covering a shift quickly without forcing a small team into enterprise scheduling software.",
        "details": [
            ("What it is", "A focused handoff workflow", "The app creates a shift card, distributes a claim route, and packages the acceptance back into a cleaner manager-facing result."),
            ("Why it matters", "Shift swaps are usually noisy and fragmented", "Text threads and ad hoc messages create uncertainty. This app exists to give the exchange a clearer shape."),
            ("Where it fits", "Hourly teams and local operations", "It is most useful where people already know each other and just need a better mobile process to cover open shifts."),
        ],
        "gallery": [
            ("/shift-swap-liaison/assets/create.png", "Shift creation screen", "The creation step captures the shift details in a format ready for handoff."),
            ("/shift-swap-liaison/assets/share.png", "Shift sharing screen", "The share state produces the app-native QR or link that teammates use to claim the shift."),
            ("/shift-swap-liaison/assets/accepted.png", "Shift accepted screen", "Acceptance is reflected directly in the app so the handoff stops being ambiguous."),
        ],
        "links": [
            ("Support", "/shift-swap-liaison/support/"),
            ("Privacy", "/shift-swap-liaison/privacy/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Shift Swap Liaison is strongest when the team needs a faster handoff path, not a full HR system.",
    },
    {
        "slug": "snapdeck",
        "title": "SnapDeck",
        "theme": "theme-snapdeck",
        "category": "Study Utility",
        "tagline": "Turn screenshots and PDFs into a deck you can actually study.",
        "summary": "SnapDeck converts screenshots and PDFs into question-and-answer flashcards with on-device OCR. It is built for students who want faster review, stronger retention, and a tap-first study flow without accounts, subscriptions, or online deck management.",
        "icon": "/snapdeck/assets/icon-1024.png",
        "hero_image": "/snapdeck/assets/home.jpg",
        "hero_alt": "SnapDeck home screen preview",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("OCR", "On device"),
            ("Deck storage", "Local"),
            ("Best use", "Fast review and revision"),
        ],
        "details_intro": "SnapDeck exists because students already have screenshots, packets, and PDFs. The useful move is turning that existing material into a deck without making them rebuild the content manually.",
        "details": [
            ("What it is", "A flashcard builder from captured material", "The user imports screenshots or PDFs, SnapDeck extracts text locally, and the app produces a deck they can study right away."),
            ("Why it matters", "Study preparation is usually too expensive", "A lot of revision effort goes into formatting and retyping. SnapDeck reduces that setup burden so more time goes into actual recall."),
            ("Where it fits", "School, exam prep, and focused review", "It works best for learners who want a privacy-first utility they can own once and use repeatedly."),
        ],
        "gallery": [
            ("/snapdeck/assets/home.jpg", "SnapDeck home view", "The home view makes it clear where decks come from and how quickly a user can resume studying."),
            ("/snapdeck/assets/question.jpg", "SnapDeck question card", "Study mode keeps the front of the card isolated so the user can focus on recall before peeking."),
            ("/snapdeck/assets/answer.jpg", "SnapDeck answer card", "Answers reveal in the same flow, then the user can move forward, shuffle, or restart without friction."),
        ],
        "links": [
            ("Support", "/snapdeck/support/"),
            ("Privacy", "/snapdeck/privacy/"),
            ("Accessibility", "/snapdeck/accessibility/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "SnapDeck is meant to make study material useful faster, not to become another social education platform.",
    },
    {
        "slug": "shadowfetch",
        "title": "Shadowfetch",
        "theme": "theme-shadowfetch",
        "category": "Countdown Utility",
        "tagline": "Keep the next important date steady and visible.",
        "summary": "Shadowfetch is a local-first countdown app for iPhone and iPad built around exact event timing, recurring milestones, reminder alerts, and a next-event widget. It is designed for birthdays, anniversaries, travel, deadlines, and any future date that needs to stay dependable instead of drifting into calendar clutter.",
        "icon": "/shadowfetch/assets/icon-1024.png",
        "hero_image": "/shadowfetch/assets/home.jpg",
        "hero_alt": "Shadowfetch countdown list on iPhone",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "Local on device"),
            ("Widget", "Next upcoming event"),
            ("Best use", "Milestones and deadlines"),
        ],
        "details_intro": "Shadowfetch is built as a utility, not a scrapbook. The numbers, the next date, and the event context are the product. Everything else exists to keep those three things dependable.",
        "details": [
            ("What it is", "A countdown surface for real dates", "The app keeps upcoming events sorted automatically, shows the nearest date first, and gives the user a detailed live countdown when they open an event."),
            ("Why it matters", "Most countdown apps get unreliable at the edges", "Recurring events, time zones, daylight saving shifts, and reminder timing are where countdown utilities usually get loose. Shadowfetch is shaped around those edge cases first."),
            ("Where it fits", "Birthdays, anniversaries, travel, deadlines, and launches", "It works best when the user needs one dependable place for future dates instead of scattering them across calendars, notes, and mental reminders."),
        ],
        "gallery": [
            ("/shadowfetch/assets/home.jpg", "Shadowfetch home screen", "The main list keeps the nearest event at the top and lets the next date dominate the layout."),
            ("/shadowfetch/assets/detail.jpg", "Shadowfetch countdown detail screen", "The detail view uses a live ticker for the exact countdown while still showing recurrence, timezone, and reminder context."),
            ("/shadowfetch/assets/empty.jpg", "Shadowfetch empty state", "The first-run state stays clean and direct so the user can create an event immediately."),
        ],
        "links": [
            ("Support", "/shadowfetch/support/"),
            ("Privacy", "/shadowfetch/privacy/"),
            ("Accessibility", "/shadowfetch/accessibility/"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Shadowfetch is meant to be a steady countdown utility with strong timing behavior, not a noisy lifestyle dashboard.",
    },
    {
        "slug": "text-cleanse",
        "title": "Text Cleanse",
        "theme": "theme-text-cleanse",
        "category": "Text Utility",
        "tagline": "Clean text for prompts, forms, and review replies.",
        "summary": "Text Cleanse is a focused iOS utility for normalizing text before it moves into prompts, forms, App Store replies, or cleaner production copy. It exists to remove invisible formatting mess, inconsistent spacing, and low-grade text friction before that mess spreads downstream.",
        "icon": "/assets/portfolio/text-cleanse-mark.svg",
        "hero_image": "/assets/portfolio/text-cleanse-mark.svg",
        "hero_alt": "Text Cleanse app mark",
        "metrics": [
            ("Platform", "iPhone and iPad"),
            ("Storage", "Local"),
            ("Best use", "Prompt and copy cleanup"),
            ("Account", "None"),
        ],
        "details_intro": "This is a narrow tool, but a useful one. Bad text formatting causes wasted time across prompts, forms, review responses, and publishing surfaces.",
        "details": [
            ("What it is", "A cleanup layer before text leaves the device", "The user drops in messy text and gets back cleaner output that is easier to use in professional or operational contexts."),
            ("Why it matters", "Small text problems create repeat friction", "Invisible characters, weird spacing, and broken punctuation are minor individually but expensive when they keep reappearing."),
            ("Where it fits", "AI prompts, forms, support copy, and release work", "It is useful anywhere rough text needs to become dependable output quickly."),
        ],
        "gallery": [],
        "links": [
            ("Contact", "mailto:the Shadowfetch support page?subject=Text%20Cleanse"),
            ("Back to portfolio", "/"),
        ],
        "footer_note": "Text Cleanse is built as a utility layer for cleaner output, not as a writing assistant pretending to be a platform.",
    },
]


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Shadowfetch</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#0a0e17">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title} | Shadowfetch">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title} | Shadowfetch">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image}">
  <meta name="twitter:site" content="@MrBobCorbin">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="icon" href="{icon}" type="{icon_type}">
  <link rel="stylesheet" href="/assets/styles.css?v=20260411d">
  <link rel="stylesheet" href="/assets/portfolio-home.css?v=20260411d">
  <link rel="stylesheet" href="/assets/product-detail.css?v=20260411d">
</head>
<body class="portfolio-home product-detail {theme}">
  <header class="home-header">
    <div class="shell">
      <a class="home-brand" href="/" aria-label="Shadowfetch home">
        <span class="home-brand-mark">SF</span>
        <span class="home-brand-copy">
          <strong>Shadowfetch</strong>
          <small>{title}</small>
        </span>
      </a>
      <nav class="home-nav" aria-label="{title} navigation">
        {nav}
      </nav>
    </div>
  </header>

  <main class="product-main">
    <section class="product-hero">
      <div class="hero-grid"></div>
      <div class="shell product-hero-layout">
        <article class="product-card">
          <p class="product-kicker">{category}</p>
          <h1 class="product-title">{tagline}</h1>
          <p class="product-summary">{summary}</p>
          <div class="product-actions">
            {actions}
          </div>
          <ul class="product-bullets">
            {bullet_list}
          </ul>
        </article>
        <aside class="product-panel">
          <div class="product-visual-wrap">
            <img class="product-icon" src="{icon}" alt="{title} icon">
            <img class="product-preview" src="{hero_image}" alt="{hero_alt}">
          </div>
          <dl class="product-meta">
            {meta}
          </dl>
        </aside>
      </div>
    </section>

    <section class="product-sections">
      <div class="shell">
        <section class="product-section">
          <div class="product-section-heading">
            <div>
              <p class="eyebrow">Explanation</p>
              <h2>What this app is actually for.</h2>
            </div>
            <p>{details_intro}</p>
          </div>
          <div class="detail-grid">
            {detail_cards}
          </div>
        </section>
        {gallery_section}
        <section class="product-section">
          <div class="product-surface">
            <div class="product-section-heading">
              <div>
                <p class="eyebrow">Links</p>
                <h2>Open the right path.</h2>
              </div>
              <p>Support, policy, accessibility, and portfolio links stay direct so the page works as a clean public product surface.</p>
            </div>
            <div class="product-links">
              {links}
            </div>
            <div class="product-footer">
              <p class="product-footer-note">{footer_note}</p>
            </div>
          </div>
        </section>
      </div>
    </section>
  </main>

  <footer class="home-footer">
    <div class="shell home-footer-inner">
      <p>© <span data-current-year></span> Shadowfetch</p>
      <p>{footer_note}</p>
    </div>
  </footer>

  <script src="/assets/app.js?v=20260411d"></script>
</body>
</html>
"""


def absolute(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://") or url.startswith("mailto:"):
        return url
    return f"{SITE}{url}"


def icon_type(path: str) -> str:
    return "image/svg+xml" if path.endswith(".svg") else "image/png"


def render_nav(product: dict) -> str:
    items = [('<a href="/">Home</a>')]
    for label, href in product["links"]:
        if href.startswith("mailto:") or label == "Back to portfolio":
            continue
        items.append(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>')
    return "\n        ".join(items)


def render_actions(product: dict) -> str:
    rendered = []
    first = True
    for label, href in product["links"][:3]:
        cls = "product-action product-action-primary" if first else "product-action product-action-secondary"
        rendered.append(f'<a class="{cls}" href="{escape(href, quote=True)}">{escape(label)}</a>')
        first = False
    return "\n            ".join(rendered)


def render_meta(product: dict) -> str:
    return "\n            ".join(
        f"<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>"
        for label, value in product["metrics"]
    )


def render_detail_cards(product: dict) -> str:
    return "\n            ".join(
        (
            '<article class="detail-card">'
            f'<span class="detail-label">{escape(label)}</span>'
            f"<h3>{escape(title)}</h3>"
            f'<p class="detail-copy">{escape(copy)}</p>'
            "</article>"
        )
        for label, title, copy in product["details"]
    )


def render_gallery(product: dict) -> str:
    if not product["gallery"]:
        return ""
    figures = "\n            ".join(
        (
            "<figure>"
            f'<img src="{escape(src, quote=True)}" alt="{escape(alt)}">'
            f"<figcaption>{escape(caption)}</figcaption>"
            "</figure>"
        )
        for src, alt, caption in product["gallery"]
    )
    return f"""
        <section class="product-section">
          <div class="product-section-heading">
            <div>
              <p class="eyebrow">Screens</p>
              <h2>How the product shows up on device.</h2>
            </div>
            <p>These screens give the product page more weight and make the app feel real instead of abstract.</p>
          </div>
          <div class="product-gallery">
            {figures}
          </div>
        </section>"""


def render_links(product: dict) -> str:
    return "\n              ".join(
        f'<a href="{escape(href, quote=True)}">{escape(label)}</a>'
        for label, href in product["links"]
    )


def write_product_page(product: dict) -> None:
    path = ROOT / product["slug"] / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    html = PAGE_TEMPLATE.format(
        title=escape(product["title"]),
        description=escape(product["summary"]),
        canonical=escape(absolute(f"/{product['slug']}/"), quote=True),
        og_image=escape(absolute(product["hero_image"]), quote=True),
        icon=escape(product["icon"], quote=True),
        icon_type=icon_type(product["icon"]),
        theme=escape(product["theme"]),
        nav=render_nav(product),
        category=escape(product["category"]),
        tagline=escape(product["tagline"]),
        summary=escape(product["summary"]),
        actions=render_actions(product),
        bullet_list="\n            ".join(f"<li>{escape(label)}: {escape(value)}</li>" for label, value in product["metrics"][:3]),
        hero_image=escape(product["hero_image"], quote=True),
        hero_alt=escape(product["hero_alt"]),
        meta=render_meta(product),
        details_intro=escape(product["details_intro"]),
        detail_cards=render_detail_cards(product),
        gallery_section=render_gallery(product),
        links=render_links(product),
        footer_note=escape(product["footer_note"]),
    )
    path.write_text(html, encoding="utf-8")


def main() -> None:
    for product in PRODUCTS:
        write_product_page(product)


if __name__ == "__main__":
    main()
