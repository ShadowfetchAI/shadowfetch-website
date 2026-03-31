import {
  clampDayNumber,
  computeDayNumber,
  loadBibleEdition,
  loadReading,
  normalizeCanon,
  normalizeStartDate,
  selectPlan,
} from "../_lib/bible.js";

export async function onRequestGet(context) {
  try {
    const url = new URL(context.request.url);
    const canon = normalizeCanon(url.searchParams.get("canon"));
    const startDate = normalizeStartDate(url.searchParams.get("start_date"));
    const explicitDay = url.searchParams.get("day");

    const data = await loadBibleEdition(context);
    const plan = selectPlan(data, canon);
    const totalDays = Number(plan?.total_days || 365);
    const dayNumber = explicitDay
      ? clampDayNumber(explicitDay, totalDays)
      : computeDayNumber(startDate, new Date(), totalDays);
    const reading = await loadReading(context, canon, dayNumber);

    return Response.json(
      {
        ok: true,
        generatedAt: data.generated_at || null,
        dayNumber,
        startDate,
        canon,
        site: data.site || {},
        plan: {
          label: plan?.label || null,
          translation: plan?.translation || null,
          totalDays,
        },
        reading,
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
        error: "Could not load today's reading.",
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
