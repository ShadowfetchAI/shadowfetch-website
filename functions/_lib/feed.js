const FEED_PATH = "/assets/data/feed.json";

export async function loadFeedSnapshot(context) {
  const assetUrl = new URL(FEED_PATH, context.request.url);
  const response = await context.env.ASSETS.fetch(assetUrl);
  if (!response.ok) {
    throw new Error(`Could not load feed snapshot: ${response.status}`);
  }

  return response.json();
}

export function clampInt(value, minimum, maximum, fallback) {
  const parsed = Number.parseInt(String(value || ""), 10);
  if (Number.isNaN(parsed)) {
    return fallback;
  }

  return Math.max(minimum, Math.min(maximum, parsed));
}
