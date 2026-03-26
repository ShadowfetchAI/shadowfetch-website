# Cloudflare Migration

ShadowFetch can move off GitHub Pages cleanly without rewriting the site.

## What is already wired

- `wrangler.jsonc` configures a Cloudflare Pages project whose build output is `dist/`
- `scripts/build_dist.py` packages the generated site into `dist/`
- `functions/api/visit.js` provides a runtime visitor counter endpoint
- `functions/api/meta.js` exposes runtime site metadata
- `functions/api/latest.js` exposes the latest feed snapshot as an API
- `migrations/0001_shadowfetch.sql` seeds the optional D1 table for the visitor counter

## Build flow

```bash
python3 scripts/build_feed.py
python3 scripts/build_pages.py
python3 scripts/build_dist.py
```

Or, after installing Wrangler:

```bash
npm install
npm run build
```

## Local Cloudflare development

```bash
npm install
npm run build
npx wrangler pages dev dist
```

If you have created and bound a D1 database, local development can use it too:

```bash
npx wrangler pages dev dist --d1 SITE_DB=<DATABASE_ID>
```

## Production cutover

1. Log in with Wrangler or provide a scoped Cloudflare Pages token.
2. Create a Pages project in Cloudflare.
3. Deploy the built `dist/` directory.
4. Add the custom domain in Cloudflare Pages.
5. Once the new site is serving correctly, disable GitHub Pages.

Example direct deploy:

```bash
npm install
npm run build
CLOUDFLARE_ACCOUNT_ID=<ACCOUNT_ID> npx wrangler pages deploy dist --project-name=shadowfetch-news
```

## Optional D1 setup

Create the database, then add its IDs to `wrangler.jsonc` under `d1_databases`.

After that, apply the schema:

```bash
npx wrangler d1 execute shadowfetch-news --remote --file=./migrations/0001_shadowfetch.sql
```

If D1 is not configured yet, the new counter API falls back to CounterAPI so the site still works.

## Notes

- The `functions/` directory is only compiled when deploying with Wrangler.
- `dist/_headers` is generated automatically for basic caching and security headers.
- The repository workflow now expects two GitHub secrets for automated Cloudflare deploys:
  - `CLOUDFLARE_API_TOKEN`
  - `CLOUDFLARE_ACCOUNT_ID`
- If the old Cloudflare Git integration stays broken, GitHub Actions direct deploys are the reliable path forward.
