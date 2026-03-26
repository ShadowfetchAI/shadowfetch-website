import { readCounter } from "../_lib/counter.js";
import { loadFeedSnapshot } from "../_lib/feed.js";

export async function onRequestGet(context) {
  try {
    const [feed, counter] = await Promise.all([
      loadFeedSnapshot(context),
      readCounter(context.env).catch(() => null)
    ]);

    return Response.json(
      {
        ok: true,
        generatedAt: feed.generated_at || null,
        latestCount: Array.isArray(feed.latest) ? feed.latest.length : 0,
        sectionCount: Array.isArray(feed.sections) ? feed.sections.length : 0,
        sourceCount: Number(feed.total_sources || 0),
        counter
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
        error: "Could not build site metadata."
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
