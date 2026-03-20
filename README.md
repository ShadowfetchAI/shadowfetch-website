# ShadowFetch News

ShadowFetch News is a multi-page newsroom with a late-breaking front page, topic hubs, source profiles,
story briefs, coverage clusters, a searchable archive, and a top-of-page visitor counter plus social links.

## Site structure

- `index.html` is the front page.
- `latest/index.html` is the denser late-breaking archive view.
- `sections/index.html` is the desk directory.
- `topics/index.html` is the topic hub index.
- `sources/index.html` is the source directory.
- `search/index.html` is the client-side search page.
- `archive/index.html` is the dated archive index.
- `roundups/today/index.html` is the generated daily roundup page.
- `sections/<section-key>/index.html` pages are generated desk pages for each section.
- `topics/<topic-key>/index.html` pages group broader story lines across the site.
- `sources/<source-key>/index.html` pages show each feed source and its recent footprint.
- `briefs/<story-slug>/index.html` pages are internal story briefs with related links.
- `coverage/<cluster-slug>/index.html` pages group developing stories.
- `archive/<YYYY-MM-DD>/index.html` pages store dated story sets.
- `about/index.html` explains the project and follow links.
- `assets/styles.css` contains the shared visual system.
- `assets/app.js` contains the social links, visitor counter logic, filter controls, and search behavior.
- `assets/data/feed-config.json` defines the section list and source feeds.
- `assets/data/feed.json` is the generated feed dataset consumed by the site.
- `assets/data/search-index.json` is the generated search dataset for the search page.
- `scripts/build_feed.py` fetches the configured feeds and prepares the JSON feed dataset.
- `scripts/build_pages.py` generates the site shell, all section/topic/source/detail pages, the search index, `sitemap.xml`, and `robots.txt`.

## Visitor counter

The visitor counter uses CounterAPI in two ways:

- The page generator asks CounterAPI for the current total so the static HTML ships with a visible number.
- The browser enhances that value and increments the public site-wide counter once per session.
- If the counter service is unavailable, the static site still renders without getting stuck in a loading state.

## Refresh the feed locally

```bash
python3 scripts/build_feed.py
python3 scripts/build_pages.py
```

That writes a fresh `assets/data/feed.json`, regenerates the HTML pages across the site, rebuilds `assets/data/search-index.json`, and refreshes the sitemap files.

## Publishing note

The site is deployed from generated output:

- GitHub Actions refreshes feed data before deployment and on a schedule.
- GitHub Actions also regenerates every HTML page, the search index, and sitemap files.
- The deployed site ships with the current stories already embedded into the page HTML.

## Feed strategy

The source mix leans on:

- official institutional feeds where practical
- long-running publisher feeds for broad coverage
- topic-specific feeds for areas like security, science, politics, business, and culture

## Next upgrades

- publish original editor-written notes and roundups
- add newsletter capture and analytics-backed most-read modules
- introduce richer manual curation controls for the homepage
