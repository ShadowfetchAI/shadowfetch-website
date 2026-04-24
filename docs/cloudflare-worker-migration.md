# Shadowfetch Cloudflare-Only Migration

This migration keeps all public app URLs intact while removing GitHub from the publish path.

## Goal

Move from the current Git-backed Cloudflare Pages project to a Cloudflare Worker with Static Assets, while keeping the same public URLs:

- `https://www.shadowfetch.com/arbiter/`
- `https://www.shadowfetch.com/daily-word-journey/`
- `https://www.shadowfetch.com/fast-pdf/`
- `https://www.shadowfetch.com/hush/`
- `https://www.shadowfetch.com/receipt-to-pdf/`
- `https://www.shadowfetch.com/renew-guard/`
- `https://www.shadowfetch.com/route-pay/`
- `https://www.shadowfetch.com/shift-swap-liaison/`

The Apple-facing marketing, support, and privacy URLs do not change.

## Why

- The current Pages project is Git-integrated, so GitHub keeps controlling production deploys.
- Cloudflare does not allow switching a Git-integrated Pages project into Direct Upload later.
- Cloudflare does support disabling automatic Pages deployments and migrating to Workers Static Assets.

## Current Worker Path

- Worker config: `wrangler.worker.jsonc`
- Production cutover config: `wrangler.worker.prod.jsonc`
- Worker bundle script: `scripts/build_worker_bundle.sh`
- Generated worker output: `.cloudflare/worker/`
- Preview deployment: `https://shadowfetch-site.robertcorbin84.workers.dev`

The worker path compiles the current `functions/` folder into a Worker and serves the existing `dist/` directory as static assets.
`wrangler.worker.jsonc` is intentionally preview-safe and does not try to claim the production hostnames.
`wrangler.worker.prod.jsonc` is the explicit cutover config for `www.shadowfetch.com` and `shadowfetch.com`.

## Commands

Build the Worker bundle:

```bash
./scripts/build_worker_bundle.sh
```

Dry-run the Worker deploy:

```bash
npx wrangler deploy --config wrangler.worker.jsonc --dry-run
```

Deploy the Worker:

```bash
npx wrangler deploy --config wrangler.worker.jsonc
```

Deploy the Worker with the production `www` hostname:

```bash
npx wrangler deploy --config wrangler.worker.prod.jsonc
```

## Cutover Plan

1. Disable automatic deployments for the existing Pages project.
2. Build and dry-run the Worker deployment.
3. Deploy the Worker to `workers.dev`.
4. Verify all app pages, support pages, privacy pages, and API routes on the Worker deployment.
5. Attach `www.shadowfetch.com` to the Worker.
6. Re-verify every Apple-facing URL.
7. Keep the Pages project untouched until the Worker serves production traffic cleanly.

## Current Status

- The Worker preview is live and serving all product, support, privacy, and API routes correctly.
- `www.shadowfetch.com` is now attached to the Worker service `shadowfetch-site`.
- The Pages project no longer owns the production `www` hostname.
- Bare `shadowfetch.com` still redirects to `www.shadowfetch.com` at the zone level, so Apple-facing URLs remain stable.
- Future production site updates should deploy to the Worker, not to Pages.

## Verification Checklist

- Homepage loads
- All product pages load
- All support pages load
- All privacy pages load
- Slashless URLs redirect correctly
- `/api/day`
- `/api/latest`
- `/api/markets`
- `/api/meta`
- `/api/progress`
- `/api/send-devotionals`
- `/api/signup`
- `/api/sports`
- `/api/unsubscribe`
- `/api/visit`
- `/api/weather`

## Important Note

This is intentionally a parallel deploy path. The Worker can be validated fully before the existing Pages project is removed.
