#!/usr/bin/env python3

from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://www.shadowfetch.com"
CONTACT_EMAIL = "the Shadowfetch support page"
LAST_UPDATED = "April 11, 2026"


PRODUCTS = [
    {
        "slug": "fast-pdf",
        "title": "Fast PDF",
        "theme": "info-theme-fast-pdf",
        "icon": "/fast-pdf/assets/icon-1024.png",
        "hero_copy": "Rapid local PDF capture for iPhone and iPad with direct Files export and no vendor cloud account.",
        "support_intro": "If you need help, want to report a bug, or have an App Review question about Fast PDF, use the public support page.",
        "support_faqs": [
            ("Where do the PDFs go?", "Single capture exports through the Files sheet. Rapid capture writes each PDF into the approved Fast PDF folder."),
            ("Why does rapid capture need a folder first?", "Rapid mode is built to avoid reopening Files between shots, so the app needs one approved destination before the run starts."),
            ("Does the app use iCloud Drive?", "Only if the user chooses an iCloud Drive location in Files. Any sync is then handled by Apple, not Shadowfetch."),
            ("Why is camera access required?", "Fast PDF needs the device camera to capture paper pages before turning them into PDFs."),
        ],
        "support_checks": [
            "Confirm camera permission is allowed for Fast PDF in iOS Settings.",
            "If rapid capture stops saving, reselect the Fast PDF folder so iOS refreshes the folder bookmark.",
            "If a save fails, confirm the chosen Files destination still exists and has free space.",
        ],
        "privacy_short": "Fast PDF works locally on the device. It does not require an account and does not upload document images or PDFs to a Shadowfetch-operated server.",
        "privacy_badge": "No data collected",
        "privacy_sections": [
            ("What the app stores", "Fast PDF stores local working state on device, including rapid-session counters and an optional Files folder bookmark when the user approves a destination."),
            ("Camera access", "Camera access is used only to capture paper pages the user wants to turn into PDFs."),
            ("Files and iCloud Drive", "The user chooses where PDFs go. If the user selects iCloud Drive, Apple handles that sync through the user’s Apple account."),
            ("Analytics and tracking", "Fast PDF does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share Fast PDF document data because the app does not collect it on a vendor backend."),
        ],
    },
    {
        "slug": "grandmas-cookbook",
        "title": "Grandma's Cookbook",
        "theme": "info-theme-grandmas-cookbook",
        "icon": "/grandmas-cookbook/assets/icon-1024.png",
        "hero_copy": "A local-first family recipe archive for iPhone and iPad built around long PDFs, OCR repair, and recipe memory.",
        "support_intro": "If you need help preserving a cookbook volume, fixing OCR, or understanding the archive flow, use the public support page.",
        "support_faqs": [
            ("What does the app save?", "It stores page images, OCR text, corrected text, notes, tags, and the long PDF for each cookbook volume."),
            ("Can I correct bad OCR?", "Yes. Each saved page has an editing surface for recipe names, ingredients, corrected text, notes, and tags."),
            ("Can I search across several cookbooks?", "Yes. Search covers recipe names, ingredient text, OCR text, and family notes across the archive."),
            ("Do I need an account?", "No. Grandma’s Cookbook is local-first and does not require sign-in."),
        ],
        "support_checks": [
            "Confirm camera permission is enabled if scanning does not open.",
            "Confirm photo access is enabled if importing existing recipe photos fails.",
            "If text quality is weak, open the page editor and correct the recipe fields directly.",
        ],
        "privacy_short": "Grandma’s Cookbook stores scans, PDFs, corrected text, notes, and search data on the user’s device. The app does not upload family recipe content to a Shadowfetch server.",
        "privacy_badge": "No data collected",
        "privacy_sections": [
            ("What the app stores", "The app stores scanned page images, imported recipe photos, OCR text, corrected recipe text, cookbook titles, notes, tags, and generated PDFs locally on the device."),
            ("Camera and photo access", "Camera permission is used to scan recipe pages. Photo library access is used only when the user imports recipe images already on the device."),
            ("On-device OCR", "Text recognition is performed with Apple’s built-in frameworks on device. Grandma’s Cookbook does not run a hosted OCR service."),
            ("Analytics and tracking", "The app does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share cookbook data because the app does not collect that data on a vendor backend."),
        ],
    },
    {
        "slug": "hush",
        "title": "Hush",
        "theme": "info-theme-hush",
        "icon": "/assets/portfolio/hush-icon.png",
        "hero_copy": "Offline text encryption for iPhone and iPad with no account, no hosted inbox, and no chat network to join.",
        "support_intro": "If you need help with Hush, want to report a problem, or have a privacy question, use the public support page.",
        "support_faqs": [
            ("Does Hush send messages for me?", "No. Hush encrypts and decrypts text locally. The user copies the encrypted result into another app manually."),
            ("Does Hush need an account?", "No. There is no account creation, hosted inbox, or server-side delivery inside Hush."),
            ("How do two people use it?", "Both people agree on the same shared secret phrase. The sender encrypts with that phrase and the receiver decrypts locally with the same phrase."),
            ("Does Hush store messages in the cloud?", "No. Hush is a local encryption utility, not a hosted messaging service."),
        ],
        "support_checks": [
            "Make sure the same shared secret phrase is used on both devices.",
            "If decryption fails, verify there are no extra spaces or punctuation changes in the secret phrase.",
            "If copied text looks incomplete, paste it into a plain text field first to confirm the full encrypted message moved over.",
        ],
        "privacy_short": "Hush is designed to work locally on the device. It does not require an account, does not operate a hosted message inbox, and does not upload text to a Shadowfetch server.",
        "privacy_badge": "Local only",
        "privacy_sections": [
            ("What the app stores", "Hush stores the user’s working text and settings locally on device only for the purpose of local encryption and decryption flows."),
            ("How encryption works", "Text is encrypted and decrypted locally with a shared secret phrase. Hush is not a messaging network and does not deliver messages for the user."),
            ("Analytics and tracking", "Hush does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share Hush text because the app does not collect it on a vendor backend."),
        ],
    },
    {
        "slug": "receipt-to-pdf",
        "title": "Receipt to PDF",
        "theme": "info-theme-receipt-to-pdf",
        "icon": "/assets/portfolio/receipt-to-pdf-icon.png",
        "hero_copy": "Private receipt scanning for iPhone and iPad with on-device PDF export and straightforward Files integration.",
        "support_intro": "If you need help with receipt capture, export, or privacy behavior in Receipt to PDF, use the public support page.",
        "support_faqs": [
            ("How does export work?", "Receipts are scanned into PDFs on device, then exported through Apple’s Files system."),
            ("Can I rename the PDF before saving?", "Yes. Receipt to PDF is built around a clean rename-and-save flow before export is finalized."),
            ("Does the app store receipts online?", "No. The app is local-first and does not use a Shadowfetch cloud inbox."),
            ("Why does it need camera access?", "Camera access is required to scan the receipt image before generating the PDF."),
        ],
        "support_checks": [
            "Confirm camera permission is enabled if the scanner does not open.",
            "If export fails, verify the chosen Files destination is available and has enough free space.",
            "If the PDF looks weak, rescan with better contrast and flatter framing.",
        ],
        "privacy_short": "Receipt to PDF processes receipt images on the device, exports PDFs locally, and does not require a Shadowfetch account or vendor cloud storage.",
        "privacy_badge": "Private by default",
        "privacy_sections": [
            ("What the app stores", "Receipt to PDF stores the user’s current receipt capture and local PDF output on device until the user exports or removes it."),
            ("Camera and Files access", "Camera access is used to scan receipts. Files access is used only when the user exports the finished PDF to a chosen destination."),
            ("Analytics and tracking", "The app does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share receipt data because the app does not collect it on a vendor backend."),
        ],
    },
    {
        "slug": "renew-guard",
        "title": "Renew Guard",
        "theme": "info-theme-renew-guard",
        "icon": "/assets/portfolio/renew-guard-icon.png",
        "hero_copy": "A local-first subscription renewal tracker for iPhone and iPad with reminders, OCR-assisted intake, and optional calendar support.",
        "support_intro": "If you need help with reminders, screenshot intake, or subscription records in Renew Guard, use the public support page.",
        "support_faqs": [
            ("What does Renew Guard track?", "It stores subscription names, costs, billing cycles, renewal dates, notes, and optional links locally on device."),
            ("Can I import screenshots?", "Yes. If the user chooses to import a confirmation screenshot, Renew Guard can parse that image on device with Apple Vision."),
            ("Does it require an account?", "No. Renew Guard is local-first and does not create a vendor account."),
            ("Can it add renewal reminders to the calendar?", "Yes. Calendar access is optional and used only when the user explicitly creates a calendar reminder."),
        ],
        "support_checks": [
            "Confirm notification permission is enabled if reminders are not appearing.",
            "If screenshot intake is weak, use clearer images with visible service name, price, and renewal date.",
            "If calendar reminders fail, check that calendar permission is allowed in iOS Settings.",
        ],
        "privacy_short": "Renew Guard stores subscription records locally on the user’s device, does not require an account, and does not upload renewal data to a Shadowfetch backend.",
        "privacy_badge": "No vendor backend",
        "privacy_sections": [
            ("What the app stores", "Renew Guard stores subscription names, costs, billing cycles, dates, notes, optional links, and optional screenshot-derived fields locally on the device."),
            ("Photos and OCR", "If the user imports a screenshot, the image is processed on device using Apple Vision to help fill subscription fields."),
            ("Calendar and notifications", "Calendar access and local notifications are optional system features used only when the user chooses reminder-related actions."),
            ("Analytics and tracking", "Renew Guard does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share subscription data because the app does not collect it on a vendor backend."),
        ],
        "accessibility_intro": "Renew Guard uses SwiftUI system controls and is intended to work cleanly with standard iOS accessibility settings.",
        "accessibility_sections": [
            ("Current expectations", [
                "Dark interface support.",
                "Larger text support through standard SwiftUI and iOS scaling behavior.",
                "A task flow that does not depend on audio or video content.",
            ]),
            ("Before claiming additional labels", [
                "Test the full flow before declaring support for VoiceOver, Voice Control, Differentiate Without Color Alone, Sufficient Contrast, or Reduced Motion in App Store Connect.",
                "Validate common tasks: add a subscription, edit one, import a screenshot, review history, and use settings.",
            ]),
        ],
    },
    {
        "slug": "shift-swap-liaison",
        "title": "Shift Swap Liaison",
        "theme": "info-theme-shift-swap-liaison",
        "icon": "/shift-swap-liaison/assets/icon-1024.png",
        "hero_copy": "Local-first shift handoff coordination with app-only QR and link claiming, plus manager-ready follow-up.",
        "support_intro": "If you need help with shift invites, claims, or manager communication behavior in Shift Swap Liaison, use the public support page.",
        "support_faqs": [
            ("Does the manager need the app?", "No. The manager only needs the confirmation use the public support page for or message the user sends from the app."),
            ("Do coworkers need the app?", "Yes. The QR code and deep link are app-only and open the claim flow inside Shift Swap Liaison."),
            ("Does the app send anything automatically?", "No. The app opens Apple’s system Mail, Messages, or share surfaces so the user confirms before anything is sent."),
            ("Does it connect to scheduling software?", "No. Shift Swap Liaison is intentionally local-first and does not integrate with enterprise scheduling platforms."),
        ],
        "support_checks": [
            "Make sure the teammate opening the link has Shift Swap Liaison installed.",
            "If a QR code is not recognized, retest with better camera focus and lighting.",
            "If the manager use the public support page for flow looks wrong, verify the saved manager details in the app profile first.",
        ],
        "privacy_short": "Shift Swap Liaison does not create user accounts or run a team backend. It stores handoff data locally on device and uses Apple’s share and compose surfaces when the user chooses to communicate.",
        "privacy_badge": "Local-first workflow",
        "privacy_sections": [
            ("What the app stores", "The app stores saved user details, default manager details, shift request history, shift content, and communication preferences locally on device."),
            ("Camera access", "If the user enables camera access, it is used only to scan app-only QR codes for shift requests and status updates."),
            ("Sharing and communication", "When the user chooses to send a shift invite or acceptance, the app uses Apple’s Mail, Messages, or system share surfaces. Nothing is sent without the user confirming."),
            ("Analytics and tracking", "Shift Swap Liaison does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share shift data because the app does not collect it on a vendor backend."),
        ],
    },
    {
        "slug": "snapdeck",
        "title": "SnapDeck",
        "theme": "info-theme-snapdeck",
        "icon": "/snapdeck/assets/icon-1024.png",
        "hero_copy": "A privacy-first flashcard builder for screenshots and PDFs with on-device OCR and focused study controls.",
        "support_intro": "If you need help with imports, deck generation, or App Store review questions for SnapDeck, use the public support page.",
        "support_faqs": [
            ("How do I make a deck?", "Import screenshots from Photos or PDFs from Files, then generate flashcards from the selected material."),
            ("Can I test the app without my own files?", "Yes. Open Saved Decks and use Load Demo Deck to review the full study flow immediately."),
            ("What if the imported text is weak?", "Use clearer screenshots, higher-contrast scans, or smaller packets so OCR has more readable material."),
            ("What study controls are built in?", "Study mode supports tap to reveal, Reveal Answer, Next Card, Restart, and Shuffle."),
        ],
        "support_checks": [
            "Confirm Photos access only if importing screenshots from the photo library.",
            "If PDF import fails, verify the chosen file is reachable through Files and not locked by another app.",
            "If deck output is noisy, reduce the amount of mixed or low-contrast source material in a single import.",
        ],
        "privacy_short": "SnapDeck is designed as a privacy-first study utility. It does not require an account, does not include advertising or tracking, and keeps imported material and generated decks local to the device.",
        "privacy_badge": "Privacy-first study tool",
        "privacy_sections": [
            ("What the app accesses", "SnapDeck accesses only the screenshots or PDFs the user explicitly selects, along with locally stored deck data created from that content."),
            ("How the app uses that data", "The app extracts text on device, generates flashcards from the selected material, and stores the resulting decks locally for later review."),
            ("Data collection", "SnapDeck does not create user profiles, does not upload study material to a Shadowfetch account system, and does not track users across apps or websites."),
            ("Data sharing", "SnapDeck does not sell study data and does not share study content with third parties in the current release."),
            ("On-device storage", "Generated decks stay in the app’s local storage area unless the user deletes them or removes the app."),
        ],
        "accessibility_intro": "SnapDeck’s study flow is designed around standard SwiftUI controls and common iOS accessibility behavior.",
        "accessibility_sections": [
            ("Current expectations", [
                "Labeled controls for importing, generating decks, revealing answers, moving forward, restarting, and shuffling.",
                "A task flow that does not depend on audio or video content.",
                "Compatibility with standard iOS interface scaling and appearance settings.",
            ]),
            ("Before claiming additional labels", [
                "Validate the exact release build on supported devices before selecting App Store accessibility nutrition labels.",
                "Only claim support for a feature if users can complete SnapDeck’s common tasks with that feature enabled.",
            ]),
        ],
    },
    {
        "slug": "shadowfetch",
        "title": "Shadowfetch",
        "theme": "info-theme-shadowfetch",
        "icon": "/shadowfetch/assets/icon-1024.png",
        "hero_copy": "A local-first countdown app for iPhone and iPad with recurring events, reminders, timezone-aware timing, and a next-event widget.",
        "support_intro": "If you need help with reminders, recurring events, time-zone behavior, or the widget in Shadowfetch, use the public support page.",
        "support_faqs": [
            ("What kind of events can I add?", "Shadowfetch is built for birthdays, anniversaries, travel, deadlines, launches, and other future milestones that need a dependable countdown."),
            ("Do recurring events reset automatically?", "Yes. Yearly and monthly recurring events roll forward automatically after the current occurrence passes."),
            ("How do reminders work?", "Reminders are scheduled as local notifications on the device. If the user chooses one week before or another lead time, iPhone handles the alert without a Shadowfetch server."),
            ("How does the widget stay accurate?", "The widget reads the next event from the app’s shared local storage and lets iOS render the countdown text with system timer styles."),
            ("What is the difference between absolute time and wall time?", "Absolute time pins the event to a specific timezone-aware moment, while wall time keeps the event aligned to the local clock the user is currently standing in."),
        ],
        "support_checks": [
            "Confirm notification permission is enabled if reminder alerts are not appearing.",
            "If a background photo does not attach, verify Photos access is enabled for Shadowfetch in iOS Settings.",
            "If an event appears wrong after travel, review the event’s time behavior and pinned timezone in the edit form.",
            "If the widget looks stale, open the app once so the next-event snapshot refreshes.",
        ],
        "privacy_short": "Shadowfetch stores countdown events on the device, uses local notifications for reminder alerts, and does not require an account or upload event data to a Shadowfetch-operated server.",
        "privacy_badge": "No vendor cloud",
        "privacy_sections": [
            ("What the app stores", "Shadowfetch stores event titles, notes, dates, recurrence settings, reminder preferences, time behavior, timezone context, and optional personalization settings locally on the user’s device."),
            ("Photos access", "If the user attaches a background image to an event, Shadowfetch accesses only the photo the user explicitly selects and stores the imported copy locally for that event."),
            ("Notifications", "Reminder alerts are handled through Apple’s local notification framework. Shadowfetch does not operate a remote push server for reminders."),
            ("Widget data", "The app writes a small snapshot of the next upcoming event into an app group so the home-screen widget can show the title, notes, recurrence label, accent color, and next date."),
            ("Analytics and tracking", "Shadowfetch does not include analytics SDKs, ad SDKs, fingerprinting, or cross-app tracking."),
            ("Data sharing", "Shadowfetch does not sell, rent, or share event data because the app does not collect it on a vendor backend."),
        ],
        "accessibility_intro": "Shadowfetch uses standard SwiftUI controls, large rounded countdown typography with monospaced digits, and a content-first layout intended to stay legible under common iOS accessibility settings.",
        "accessibility_sections": [
            ("Current expectations", [
                "Large rounded countdown numbers with monospaced digits to reduce visual jitter.",
                "Support for standard iOS text scaling and dark appearance.",
                "A task flow that does not depend on audio or video content.",
                "Standard iOS controls for adding, editing, and deleting events.",
            ]),
            ("Before claiming additional labels", [
                "Validate the exact release build before selecting App Store accessibility nutrition labels.",
                "Test common tasks with VoiceOver and Larger Text enabled: create an event, edit time behavior, attach a photo, save a reminder, and review the widget.",
            ]),
        ],
    },
]


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#0a0e17">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image}">
  <meta name="twitter:site" content="@MrBobCorbin">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="icon" href="{icon}" type="{icon_type}">
  <link rel="stylesheet" href="/assets/styles.css?v=20260411e">
  <link rel="stylesheet" href="/assets/portfolio-home.css?v=20260411e">
  <link rel="stylesheet" href="/assets/product-info.css?v=20260411e">
</head>
<body class="portfolio-home product-info {theme}">
  <header class="home-header">
    <div class="shell">
      <a class="home-brand" href="/{slug}/" aria-label="{product} home">
        <span class="home-brand-mark">SF</span>
        <span class="home-brand-copy">
          <strong>{product}</strong>
          <small>{page_label}</small>
        </span>
      </a>
      <nav class="home-nav" aria-label="{product} navigation">
        {nav}
      </nav>
    </div>
  </header>

  <main class="info-main">
    <section class="info-shell">
      <article class="info-hero">
        <div class="info-copy">
          <p class="info-kicker">{page_label}</p>
          <h1>{heading}</h1>
          <p class="info-summary">{summary}</p>
          <div class="info-links">
            {links}
          </div>
        </div>
        <aside class="info-side">
          <img class="info-icon" src="{icon}" alt="{product} icon">
          <dl class="info-facts">
            {facts}
          </dl>
        </aside>
      </article>
      {content}
    </section>
  </main>

  <footer class="home-footer">
    <div class="shell home-footer-inner">
      <p>© <span data-current-year></span> Shadowfetch</p>
      <p>{footer_note}</p>
    </div>
  </footer>

  <script src="/assets/app.js?v=20260411e"></script>
</body>
</html>
"""


def icon_type(path: str) -> str:
    return "image/svg+xml" if path.endswith(".svg") else "image/png"


def absolute(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{SITE}{path}"


def mailto(subject: str) -> str:
    return f"mailto:{CONTACT_EMAIL}?subject={quote(subject)}"


def render_nav(product: dict, include_accessibility: bool) -> str:
    items = [
        f'<a href="/{product["slug"]}/">Overview</a>',
        f'<a href="/{product["slug"]}/support/">Support</a>',
        f'<a href="/{product["slug"]}/privacy/">Privacy</a>',
    ]
    if include_accessibility:
        items.append(f'<a href="/{product["slug"]}/accessibility/">Accessibility</a>')
    items.append('<a href="/">Portfolio</a>')
    return "\n        ".join(items)


def render_links(items: list[tuple[str, str]]) -> str:
    return "\n            ".join(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>' for label, href in items)


def render_facts(items: list[tuple[str, str]]) -> str:
    return "\n            ".join(f"<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>" for label, value in items)


def render_support_content(product: dict, include_accessibility: bool) -> str:
    support_mailto = mailto(f"{product['title']} support")
    faq_cards = "\n              ".join(
        f'<div class="info-list-card"><strong>{escape(q)}</strong><p>{escape(a)}</p></div>'
        for q, a in product["support_faqs"]
    )
    checklist = "\n              ".join(f"<li>{escape(item)}</li>" for item in product["support_checks"])
    links = [
        ("Overview", f'/{product["slug"]}/'),
        ("Privacy Policy", f'/{product["slug"]}/privacy/'),
    ]
    if include_accessibility:
        links.append(("Accessibility", f'/{product["slug"]}/accessibility/'))
    links.append(("Open Support", support_mailto))
    return f"""
      <article class="info-card">
        <span class="info-card-label">Direct help</span>
        <h2>Support</h2>
        <p>{escape(product['support_intro'])} <a href="{escape(support_mailto, quote=True)}">{escape(CONTACT_EMAIL)}</a>.</p>
        <div class="info-links">
          {render_links(links)}
        </div>
      </article>
      <article class="info-card">
        <span class="info-card-label">Common questions</span>
        <h2>What people usually ask.</h2>
        <div class="info-list">
          {faq_cards}
        </div>
      </article>
      <article class="info-card">
        <span class="info-card-label">Troubleshooting</span>
        <h2>First things to check.</h2>
        <ul>
          {checklist}
        </ul>
      </article>
    """


def render_privacy_content(product: dict, include_accessibility: bool) -> str:
    privacy_mailto = mailto(f"{product['title']} privacy")
    sections = []
    for title, body in product["privacy_sections"]:
        sections.append(f"<section><h2>{escape(title)}</h2><p>{escape(body)}</p></section>")
    sections_html = "\n        ".join(sections)
    privacy_links = [
        ("Overview", f'/{product["slug"]}/'),
        ("Support", f'/{product["slug"]}/support/'),
    ]
    if include_accessibility:
        privacy_links.append(("Accessibility", f'/{product["slug"]}/accessibility/'))
    return f"""
      <article class="info-card">
        <span class="info-badge">{escape(product['privacy_badge'])}</span>
        <h2>Privacy Policy</h2>
        <p>Last updated: {LAST_UPDATED}</p>
        <p>{escape(product['privacy_short'])}</p>
        {sections_html}
        <section>
          <h2>Contact</h2>
          <p>For privacy questions, use the public support page for <a href="{escape(privacy_mailto, quote=True)}">{escape(CONTACT_EMAIL)}</a>.</p>
        </section>
      </article>
      <article class="info-card">
        <span class="info-card-label">Quick links</span>
        <h2>Open the right path.</h2>
        <div class="info-links">
          {render_links(privacy_links)}
        </div>
      </article>
    """


def render_accessibility_content(product: dict) -> str:
    accessibility_mailto = mailto(f"{product['title']} accessibility")
    sections_html = []
    for title, bullets in product["accessibility_sections"]:
        items = "\n              ".join(f"<li>{escape(item)}</li>" for item in bullets)
        sections_html.append(f"<section><h2>{escape(title)}</h2><ul>{items}</ul></section>")
    return f"""
      <article class="info-card">
        <span class="info-card-label">Accessibility</span>
        <h2>Accessibility</h2>
        <p>Last updated: {LAST_UPDATED}</p>
        <p>{escape(product['accessibility_intro'])}</p>
        {' '.join(sections_html)}
        <section>
          <h2>Contact</h2>
          <p>For accessibility questions, use the public support page for <a href="{escape(accessibility_mailto, quote=True)}">{escape(CONTACT_EMAIL)}</a>.</p>
        </section>
      </article>
      <article class="info-card">
        <span class="info-card-label">Quick links</span>
        <h2>Open the right path.</h2>
        <div class="info-links">
          {render_links([
              ("Overview", f'/{product["slug"]}/'),
              ("Support", f'/{product["slug"]}/support/'),
              ("Privacy Policy", f'/{product["slug"]}/privacy/'),
          ])}
        </div>
      </article>
    """


def write_page(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def render_page(product: dict, page_kind: str) -> str:
    include_accessibility = "accessibility_sections" in product
    if page_kind == "support":
        title = f"Support | {product['title']}"
        page_label = "Support"
        heading = "Support"
        summary = product["hero_copy"]
        content = render_support_content(product, include_accessibility)
        footer_note = f"{product['title']} support page on the stable public URL."
    elif page_kind == "privacy":
        title = f"Privacy Policy | {product['title']}"
        page_label = "Privacy Policy"
        heading = "Privacy Policy"
        summary = product["privacy_short"]
        content = render_privacy_content(product, include_accessibility)
        footer_note = f"{product['title']} privacy policy on the stable public URL."
    else:
        title = f"Accessibility | {product['title']}"
        page_label = "Accessibility"
        heading = "Accessibility"
        summary = product["accessibility_intro"]
        content = render_accessibility_content(product)
        footer_note = f"{product['title']} accessibility page on the stable public URL."

    facts = [
        ("Product", product["title"]),
        ("URL", f'/{product["slug"]}/{page_kind}/'),
        ("Contact", CONTACT_EMAIL),
    ]
    if include_accessibility and page_kind != "accessibility":
        facts.append(("Accessibility", "Available"))

    link_items = [
        ("Overview", f'/{product["slug"]}/'),
        ("Support", f'/{product["slug"]}/support/'),
        ("Privacy Policy", f'/{product["slug"]}/privacy/'),
    ]
    if include_accessibility:
        link_items.append(("Accessibility", f'/{product["slug"]}/accessibility/'))

    return PAGE_TEMPLATE.format(
        title=escape(title),
        description=escape(summary),
        canonical=escape(absolute(f'/{product["slug"]}/{page_kind}/'), quote=True),
        og_image=escape(absolute(product["icon"]), quote=True),
        icon=escape(product["icon"], quote=True),
        icon_type=icon_type(product["icon"]),
        theme=escape(product["theme"]),
        slug=escape(product["slug"]),
        product=escape(product["title"]),
        page_label=escape(page_label),
        nav=render_nav(product, include_accessibility),
        heading=escape(heading),
        summary=escape(summary),
        links=render_links(link_items),
        facts=render_facts(facts),
        content=content,
        footer_note=escape(footer_note),
    )


def main() -> None:
    for product in PRODUCTS:
        write_page(ROOT / product["slug"] / "support" / "index.html", render_page(product, "support"))
        write_page(ROOT / product["slug"] / "privacy" / "index.html", render_page(product, "privacy"))
        if "accessibility_sections" in product:
            write_page(ROOT / product["slug"] / "accessibility" / "index.html", render_page(product, "accessibility"))


if __name__ == "__main__":
    main()
