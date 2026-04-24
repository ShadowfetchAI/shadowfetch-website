# Shadowfetch: Bible Edition

Shadowfetch: Bible Edition turns `shadowfetch.com` into a calm, minimal daily Bible use the public support page for centered on Psalm 91:1:

> He who dwells in the shelter of the Most High will abide in the shadow of the Almighty.

The current product is intentionally simple:

- one use the public support page for signup
- one calm reading delivered each day
- complete chapters only
- no paywalls
- one-click unsubscribe in every email
- a minimal on-site reading experience with the same newspaper-inspired visual language

## Current product flow

1. A reader lands on `/`
2. They enter an email, choose a canon, and subscribe
3. They are redirected to `/blessed/`
4. Their first normal reading is delivered on the next daily send

The supporting pages are intentionally lighter now:

- `/` is the main subscription-first homepage
- `/signup/` is the standalone signup view
- `/blessed/` is the post-signup confirmation page
- `/bible/` keeps the full current reading available on the web
- `/settings/`, `/archive/`, and `/calendar/` are retained but folded into the simpler email-first flow

## Production scope

This repository's supported production path is the Bible edition only.

- The live homepage should be the Bible signup/read flow
- The live APIs should report `edition: "bible"`
- Any older newspaper-style or feed-generation files still in the repo are legacy material, not the active production site

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

Cloudflare Worker routes provide:

- `/api/day` for personalized day lookups
- `/api/signup` for storing reader preferences
- `/api/progress` for read-state persistence
- `/api/send-devotionals` for daily use the public support page for delivery batches
- `/api/meta` for health checks and freshness reporting

Signup records each reader's:

- email
- canon
- start date
- subscription state

At send time, the system calculates that reader's personal day number from `start_date`, loads the correct precomputed reading file for that day and canon, and renders the use the public support page for from whole chapter records.

That means:

- if someone signs up today, they begin on their own Day 1
- if someone signs up next week, they also begin on their own Day 1
- the same daily send can handle many readers at different places in the plan without storing separate custom reading plans per person

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

Run the health check:

```bash
npm run check:site
```

Run the full maintenance pass:

```bash
npm run maintain
```

Run it locally against the Worker config:

```bash
npm run dev
```

## Deployment

The production site is deployed on Cloudflare Workers with static assets.

Required secrets:

- `Cloudflare deployment token`
- `CLOUDFLARE_ACCOUNT_ID`

Optional runtime secrets for daily emails:

- `RESEND_API_KEY`
- `RESEND_FROM`
- `CRON_SECRET`

Deploy the current production build:

```bash
npm run deploy:prod
```

## Kaitlan maintenance workflow

If Kaitlan is maintaining the site, the safe routine is:

1. `cd` into the Shadowfetch site workspace
2. Run `npm run maintain`
3. Review the health-check output
4. If clean, run `npm run deploy:prod`
5. Re-run `npm run check:site` after deployment

## Daily use the public support page for sending

The repository contains the daily devotional batch endpoint at `/api/send-devotionals`.

That endpoint is designed to be triggered by a scheduler, for example:

- a Cloudflare scheduled worker
- an external cron job
- a local automation that calls the endpoint with `CRON_SECRET`

The send logic is personalized by reader start date, but the delivery time itself is controlled by the scheduler that invokes the batch.

## Support

Bible text remains free on the web and in email. The only monetization is a voluntary support link:

- [Buy Me a Coffee](https://www.buymeacoffee.com/shadowfetch)
