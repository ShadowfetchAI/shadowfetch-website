import {
  computeDayNumber,
  loadBibleEdition,
  normalizeCanon,
  normalizeStartDate,
  selectPlan,
  validateEmail,
} from "../_lib/bible.js";

export async function onRequestPost(context) {
  try {
    const payload = await context.request.json();
    const email = validateEmail(payload?.email);
    const canon = normalizeCanon(payload?.canon);
    const startDate = normalizeStartDate(payload?.start_date);
    const subscribed = payload?.subscribed === false || payload?.subscribed === "0" ? 0 : 1;

    if (!email) {
      return Response.json({ ok: false, error: "A valid email address is required." }, { status: 400 });
    }

    let storageMode = "local-only";
    if (context.env.SITE_DB) {
      try {
        await context.env.SITE_DB.prepare(
          `
            INSERT INTO bible_users (email, canon, start_date, subscribed, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
              canon = excluded.canon,
              start_date = excluded.start_date,
              subscribed = excluded.subscribed,
              updated_at = CURRENT_TIMESTAMP
          `
        )
          .bind(email, canon, startDate, subscribed)
          .run();
        storageMode = "database";
      } catch (_) {
        storageMode = "local-only";
      }
    }

    const data = await loadBibleEdition(context);
    const plan = selectPlan(data, canon);
    const dayNumber = computeDayNumber(startDate, new Date(), Number(plan?.total_days || 365));

    return Response.json(
      {
        ok: true,
        email,
        canon,
        startDate,
        subscribed: Boolean(subscribed),
        storageMode,
        dayNumber,
        redirect: `/bible/?canon=${encodeURIComponent(canon)}&start_date=${encodeURIComponent(startDate)}`,
        message: "Your reading desk is ready. Today's chapters are waiting for you.",
        site: data.site || {},
      },
      {
        headers: {
          "cache-control": "no-store",
        },
      }
    );
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error: "Could not save your signup yet.",
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
