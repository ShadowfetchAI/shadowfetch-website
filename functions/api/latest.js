import { clampInt, loadFeedSnapshot } from "../_lib/feed.js";

export async function onRequestGet(context) {
  try {
    const url = new URL(context.request.url);
    const limit = clampInt(url.searchParams.get("limit"), 1, 48, 12);
    const section = String(url.searchParams.get("section") || "").trim().toLowerCase();
    const feed = await loadFeedSnapshot(context);

    const stories = Array.isArray(feed.latest) ? feed.latest : [];
    const filtered = section
      ? stories.filter((story) => String(story.section_key || "").toLowerCase() === section)
      : stories;

    return Response.json(
      {
        ok: true,
        generatedAt: feed.generated_at || null,
        section: section || null,
        count: filtered.length,
        stories: filtered.slice(0, limit)
      },
      {
        headers: {
          "cache-control": "public, max-age=60"
        }
      }
    );
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error: "Could not load the latest stories."
      },
      {
        status: 500,
        headers: {
          "cache-control": "no-store"
        }
      }
    );
  }
}
