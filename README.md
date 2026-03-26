# ShadowFetch News

ShadowFetch News is a newspaper-style digital newsroom built for fast reads, broad coverage, and source-first linking.
It combines a print-inspired front page with generated section pages, topic hubs, searchable archives, editorial briefs,
and a lightweight journal for original writing.

Live site: [www.shadowfetch.com](https://www.shadowfetch.com)

## What it is

- A multi-page news site with a front page, live wire, desks, topics, archive, and journal
- A source-first reading experience where headlines can send readers to the original publisher
- A Cloudflare-ready newsroom with prepared content and a few dynamic endpoints
- A project designed to feel nostalgic and editorial, not like a generic feed dashboard

## Highlights

- 1950s-inspired newspaper presentation with clickable digital articles
- Generated section pages for world, politics, business, technology, sports, entertainment, health, science, and more
- Topic hubs, source profiles, coverage clusters, and internal story briefs
- Searchable archive and dated archive pages
- Markdown-backed journal for original posts
- Top-of-page social links and on-site visitor counter
- Cloudflare Pages deployment with Functions and optional D1-backed counter storage

## Project structure

- `index.html`: front page
- `latest/index.html`: late-breaking wire
- `sections/`: desk landing pages
- `topics/`: topic hubs
- `sources/`: source profiles
- `briefs/`: generated story brief pages
- `coverage/`: grouped developing-story pages
- `archive/`: dated archive pages
- `journal/`: published original writing
- `content/journal/`: markdown source for journal posts
- `assets/styles.css`: shared visual system
- `assets/app.js`: client-side enhancements, search, filters, social links, counter behavior
- `assets/data/feed-config.json`: feed and desk configuration
- `scripts/build_feed.py`: fetches and prepares feed data
- `scripts/build_pages.py`: generates the HTML site and search index
- `scripts/build_dist.py`: prepares the Cloudflare deployment bundle
- `functions/api/`: Cloudflare Pages Functions for runtime APIs

## Local development

Requirements:

- Python 3.11+
- Node.js 20+

Install dependencies:

```bash
npm install
```

Build the newsroom:

```bash
npm run build
```

Run it locally with Cloudflare Pages:

```bash
npm run dev
```

## Deployment

ShadowFetch News is built for Cloudflare Pages.

- Pushes to `main` can deploy through GitHub Actions
- The scheduled workflow refreshes feed data twice an hour
- Cloudflare Functions power runtime routes like `/api/visit`, `/api/meta`, and `/api/latest`
- D1 can store the visitor counter on your own stack, with fallback support already in place

Repository secrets needed for automated deployment:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

More details: [Cloudflare migration notes](docs/cloudflare-migration.md)

## Writing and publishing

Journal entries live in `content/journal/` as markdown files.
The site generator turns them into published pages under `journal/`.

## Contributing

Contributions are welcome.
Start with [CONTRIBUTING.md](CONTRIBUTING.md) for workflow and content guidelines.

## Security

If you find a security issue, please follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
