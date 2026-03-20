# ShadowFetch News

ShadowFetch News is a GitHub Pages site for Linux, open-source, privacy, and security news. The
current build focuses on a sharper editorial homepage, live RSS-powered sections, and a clear path
to grow into a stronger publication over time.

## What is in the repo

- `index.html` contains the site shell and page structure.
- `assets/styles.css` defines the visual system and responsive layout.
- `assets/app.js` holds the feed configuration, social profile URLs, and rendering logic.
- `assets/shadowfetch-mark.svg` is the brand mark used for the favicon and header.

## Update your social links

Edit the `siteConfig.social` object in `assets/app.js`:

- `siteConfig.social.x.url`
- `siteConfig.social.bluesky.url`

Those URLs drive the follow cards on the homepage.

## GitHub Pages note

GitHub Pages is a strong fit for the visual front end and a static publication shell, but it does
not run a traditional backend. In this version, live headlines are fetched client-side from RSS
feeds through a public proxy so the site can stay simple and deploy cleanly.

For a stronger next version, move feed aggregation into scheduled GitHub Actions builds or a small
backend so the site is less dependent on browser-time feed fetching.

## Next upgrades

- Introduce original articles and roundups
- Prebuild feed data for better reliability
- Add newsletter signup and archive pages
