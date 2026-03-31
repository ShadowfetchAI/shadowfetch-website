import {
  computeDayNumber,
  loadBibleEdition,
  loadReading,
  normalizeCanon,
} from "../_lib/bible.js";
import {
  buildDevotionalSubject,
  renderDevotionalEmail,
  sendViaResend,
} from "../_lib/devotional-email.js";
import { buildUnsubscribeUrl } from "../_lib/unsubscribe.js";

export async function onRequestPost(context) {
  try {
    const auth = context.request.headers.get("authorization") || "";
    if (context.env.CRON_SECRET && auth !== `Bearer ${context.env.CRON_SECRET}`) {
      return Response.json({ ok: false, error: "Unauthorized." }, { status: 401 });
    }

    if (!context.env.SITE_DB) {
      return Response.json({ ok: false, error: "Database binding is missing." }, { status: 500 });
    }

    const data = await loadBibleEdition(context);
    const { results } = await context.env.SITE_DB.prepare(
      `
        SELECT email, canon, start_date, subscribed, last_sent_day
        FROM bible_users
        WHERE subscribed = 1
        ORDER BY email ASC
      `
    ).all();

    const sent = [];
    const skipped = [];
    const todayIso = new Date().toISOString().slice(0, 10);

    for (const user of results || []) {
      const canon = normalizeCanon(user.canon);
      const startDate = String(user.start_date || "").slice(0, 10);
      if (startDate && startDate > todayIso) {
        skipped.push({ email: user.email, reason: "not-started-yet", startDate });
        continue;
      }

      const dayNumber = computeDayNumber(user.start_date);
      if (Number(user.last_sent_day || 0) === dayNumber) {
        skipped.push({ email: user.email, reason: "already-sent", dayNumber });
        continue;
      }

      const reading = await loadReading(context, canon, dayNumber);
      const subject = buildDevotionalSubject(dayNumber);
      const unsubscribeUrl = await buildUnsubscribeUrl(context, user.email);
      const html = renderDevotionalEmail({
        site: data.site || {},
        user,
        reading,
        unsubscribeUrl,
      });

      if (context.env.RESEND_API_KEY) {
        await sendViaResend(context, { to: user.email, subject, html });
      }

      await context.env.SITE_DB.prepare(
        `
          UPDATE bible_users
          SET last_sent_day = ?, last_sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
          WHERE email = ?
        `
      )
        .bind(dayNumber, user.email)
        .run();

      sent.push({
        email: user.email,
        canon,
        dayNumber,
        mode: context.env.RESEND_API_KEY ? "sent" : "dry-run",
      });
    }

    return Response.json(
      {
        ok: true,
        generatedAt: data.generated_at || null,
        sent,
        skipped,
        dryRun: !context.env.RESEND_API_KEY,
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
        error: "Could not send the daily devotional batch.",
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
