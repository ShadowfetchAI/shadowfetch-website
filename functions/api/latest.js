import { loadBibleEdition, normalizeCanon, selectPlan } from "../_lib/bible.js";

export async function onRequestGet(context) {
  try {
    const url = new URL(context.request.url);
    const canon = normalizeCanon(url.searchParams.get("canon"));
    const limit = Math.max(1, Math.min(120, Number.parseInt(url.searchParams.get("limit") || "12", 10) || 12));
    const data = await loadBibleEdition(context);
    const plan = selectPlan(data, canon);
    const stories = Array.isArray(plan?.days) ? plan.days.slice(0, limit) : [];

    return Response.json(
      {
        ok: true,
        edition: "bible",
        generatedAt: data.generated_at || null,
        canon,
        count: stories.length,
        stories,
      },
      {
        headers: {
          "cache-control": "public, max-age=300",
        },
      }
    );
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error: "Could not load the reading archive.",
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
