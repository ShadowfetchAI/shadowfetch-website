# Shadowfetch: Bible Edition

Shadowfetch: Bible Edition repurposes `shadowfetch.com` into a calm daily Bible-reading companion built around Psalm 91:1:

> He who dwells in the shelter of the Most High will abide in the shadow of the Almighty.

The site keeps the newspaper-style layout language from the old Shadowfetch build, but the content flow is now devotional:

- daily complete-chapter readings
- canon choice for Protestant or Roman Catholic readers
- signup and preference storage through Cloudflare D1
- a PWA-friendly reading experience
- a searchable archive and year calendar
- optional daily email delivery plumbing

## Product shape

- `/` presents the daily reading and signup card
- `/bible/` is the focused reading page
- `/calendar/` shows the year plan and progress-friendly calendar
- `/archive/` exposes all 365 reading days
- `/settings/` lets readers update canon/start-date/email choices
- `/signup/` is the standalone onboarding page

## Data model

The build process bundles two public-domain scripture sources:

- Protestant plan: King James Version
- Catholic plan: Douay-Rheims

The generator precomputes:

- a 365-day reading plan for each canon
- daily quote/reflection snippets
- per-day reading payloads under `assets/data/bible-readings/`
- the main summary payload at `assets/data/bible-edition.json`

## Runtime

Cloudflare Pages Functions provide:

- `/api/day` for personalized day lookups
- `/api/signup` for storing reader preferences
- `/api/progress` for read-state persistence
- `/api/send-devotionals` for daily email delivery batches
- `/api/meta` for health checks and freshness reporting

## Local development

Requirements:

- Python 3.11+
- Node.js 20+

Install dependencies:

```bash
npm install
```

Build the site:

```bash
npm run build
```

Run it locally:

```bash
npm run dev
```

## Deployment

The production site is deployed on Cloudflare Pages using the `shadowfetch` Pages project.

Required secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Optional runtime secrets for daily emails:

- `RESEND_API_KEY`
- `RESEND_FROM`
- `CRON_SECRET`

## Support

Bible text remains free on the web and in email. The only monetization is a voluntary support link:

- [Buy Me a Coffee](https://www.buymeacoffee.com/shadowfetch)
