# ShadowFetch News

ShadowFetch News is a multi-page GitHub Pages newsroom with a prepared-feed pipeline, a late-breaking
front page, a live archive, a section directory, and a top-of-page visitor counter plus social links.

## Site structure

- `index.html` is the front page.
- `latest/index.html` is the denser late-breaking archive view.
- `sections/index.html` is the topic and source directory.
- `sections/<section-key>/index.html` pages are generated desk pages for each section.
- `about/index.html` explains the project and follow links.
- `assets/styles.css` contains the shared visual system.
- `assets/app.js` contains the social links, visitor counter logic, and page rendering.
- `assets/data/feed-config.json` defines the section list and source feeds.
- `assets/data/feed.json` is the generated snapshot consumed by the site.
- `scripts/build_feed.py` fetches the configured feeds and prepares the JSON snapshot.
- `scripts/build_pages.py` generates the section desk pages, `sitemap.xml`, and `robots.txt`.

## Visitor counter

The visitor counter uses CounterAPI from the browser so it can work on a static site:

- It increments a public site-wide counter once per browser session.
- If the session was already counted, it only reads the current total.
- If the counter service is unavailable, the UI falls back gracefully.

## Update your social links

Edit the `siteConfig.social` object in `assets/app.js`.

## Refresh the feed locally

```bash
python3 scripts/build_feed.py
python3 scripts/build_pages.py
```

That writes a fresh `assets/data/feed.json`, generates the section desk pages, and refreshes the sitemap files.

## GitHub Pages note

GitHub Pages cannot run a backend, so this repo uses a stronger static-news pattern:

- GitHub Actions generates feed data before deployment and on a schedule.
- GitHub Actions also generates the section desk pages and sitemap files.
- The deployed site reads the prepared snapshot first.
- If the snapshot is missing, the browser can still fall back to live feed fetching.

## Feed strategy

The source mix leans on:

- official institutional feeds where practical
- long-running publisher feeds for broad coverage
- topic-specific feeds for areas like security, science, politics, business, and culture

## Next upgrades

- publish original roundups and editor notes
- add newsletter and search once the content layer grows
