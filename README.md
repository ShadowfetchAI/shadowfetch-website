# ShadowFetch News

ShadowFetch News is a multi-page newsroom with a late-breaking front page, a live archive, a section
directory, and a top-of-page visitor counter plus social links.

## Site structure

- `index.html` is the front page.
- `latest/index.html` is the denser late-breaking archive view.
- `sections/index.html` is the topic and source directory.
- `sections/<section-key>/index.html` pages are generated desk pages for each section.
- `about/index.html` explains the project and follow links.
- `assets/styles.css` contains the shared visual system.
- `assets/app.js` contains the social links, visitor counter logic, and page rendering.
- `assets/data/feed-config.json` defines the section list and source feeds.
- `assets/data/feed.json` is the generated feed dataset consumed by the site.
- `templates/*.html` are the source templates for the generated top-level pages.
- `scripts/build_feed.py` fetches the configured feeds and prepares the JSON feed dataset.
- `scripts/build_pages.py` generates the top-level pages, section desk pages, `sitemap.xml`, and `robots.txt`.

## Visitor counter

The visitor counter uses CounterAPI in two ways:

- The page generator asks CounterAPI for the current total so the static HTML ships with a visible number.
- The browser enhances that value and increments the public site-wide counter once per session.
- If the counter service is unavailable, the static site still renders without getting stuck in a loading state.

## Update your social links

Edit the `siteConfig.social` object in `assets/app.js`.

## Refresh the feed locally

```bash
python3 scripts/build_feed.py
python3 scripts/build_pages.py
```

That writes a fresh `assets/data/feed.json`, regenerates the top-level pages and section desks with embedded story content, and refreshes the sitemap files.

## Publishing note

This project is deployed as a generated site, so the publishing flow is designed around prebuilt feed data:

- GitHub Actions generates feed data before deployment and on a schedule.
- GitHub Actions also generates the top-level pages, section desk pages, and sitemap files.
- The deployed site already contains the latest generated feed content in the HTML.
- If the snapshot is missing, the browser can still fall back to live feed fetching.

## Feed strategy

The source mix leans on:

- official institutional feeds where practical
- long-running publisher feeds for broad coverage
- topic-specific feeds for areas like security, science, politics, business, and culture

## Next upgrades

- publish original roundups and editor notes
- add newsletter and search once the content layer grows
