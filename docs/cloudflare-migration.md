# Cloudflare Migration

Archived note: this site no longer deploys through Cloudflare Pages or GitHub.

Current production path:

- build locally from the cached source datasets
- compile the Worker bundle
- deploy with `wrangler.worker.jsonc`
- serve production through the `shadowfetch-site` Worker on `www.shadowfetch.com`

For the active deployment and cutover details, use [cloudflare-worker-migration.md](./cloudflare-worker-migration.md).
