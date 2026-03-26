# Contributing to ShadowFetch News

Thanks for contributing.

## Before you start

- Check open issues before starting larger work
- Keep changes focused and easy to review
- Avoid unrelated cleanup in the same pull request

## Local setup

```bash
npm install
npm run build
```

If you are working on the full local preview:

```bash
npm run dev
```

## Project expectations

- Preserve the editorial feel of the site
- Keep the reading experience clean and fast
- Prefer reliable, long-running feeds over brittle or novelty sources
- Make source attribution clear
- Keep reader-facing language professional and concise

## Content changes

- Journal posts belong in `content/journal/`
- Feed and desk configuration belongs in `assets/data/feed-config.json`
- Major presentation changes should be checked on both desktop and mobile layouts

## Pull requests

- Explain what changed and why
- Note any feed, template, or deployment impact
- Include screenshots for meaningful UI changes when possible
- Mention if generated site output was rebuilt

## Commit style

Short, descriptive commit messages are preferred.
Examples:

- `Refine front page hierarchy`
- `Add source profile cards`
- `Improve Cloudflare deployment docs`
