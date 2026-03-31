import { loadBibleEdition } from "../_lib/bible.js";
import { readCounter } from "../_lib/counter.js";

export async function onRequestGet(context) {
  try {
    const [edition, counter] = await Promise.all([
      loadBibleEdition(context),
      readCounter(context.env).catch(() => null),
    ]);

    return Response.json(
      {
        ok: true,
        edition: "bible",
        generatedAt: edition.generated_at || null,
        canonCount: Array.isArray(edition.canon_choices) ? edition.canon_choices.length : 0,
        totalDays: Number(edition?.plans?.protestant?.total_days || 365),
        counter,
      },
      {
        headers: {
          "cache-control": "public, max-age=60",
        },
      }
    );
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error: "Could not build site metadata.",
      },
      {
        status: 500,
        headers: {
          "cache-control": "no-store",
        },
      }
    );
  }
}
