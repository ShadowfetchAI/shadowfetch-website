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
import {
  ensureSiteSchema,
  finishMailRun,
  openMailRun,
  recordMailEvent,
} from "../_lib/db.js";
import { buildUnsubscribeUrl } from "../_lib/unsubscribe.js";

export async function onRequestPost(context) {
  let runId = null;
  let dryRun = !context.env.RESEND_API_KEY;
  try {
    const url = new URL(context.request.url);
    const auth = context.request.headers.get("authorization") || "";
    if (context.env.CRON_SECRET && auth !== `Bearer ${context.env.CRON_SECRET}`) {
      return Response.json({ ok: false, error: "Unauthorized." }, { status: 401 });
    }

    if (!context.env.SITE_DB) {
      return Response.json({ ok: false, error: "Database binding is missing." }, { status: 500 });
    }

    await ensureSiteSchema(context.env);
    const explicitDryRun =
      url.searchParams.get("dry_run") === "1" ||
      context.request.headers.get("x-shadowfetch-dry-run") === "1";
    dryRun = explicitDryRun || !context.env.RESEND_API_KEY;
    runId = await openMailRun(context.env, {
      requestedAt: new Date().toISOString(),
      dryRun,
      note: explicitDryRun ? "daily devotional batch (dry-run)" : "daily devotional batch",
    });
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
    const failed = [];
    const todayIso = new Date().toISOString().slice(0, 10);

    for (const user of results || []) {
      const canon = normalizeCanon(user.canon);
      const startDate = String(user.start_date || "").slice(0, 10);
      if (startDate && startDate > todayIso) {
        skipped.push({ email: user.email, reason: "not-started-yet", startDate });
        await recordMailEvent(context.env, {
          runId,
          email: user.email,
          canon,
          eventType: "skipped",
          detail: `not-started-yet:${startDate}`,
        });
        continue;
      }

      const dayNumber = computeDayNumber(user.start_date);
      if (Number(user.last_sent_day || 0) === dayNumber) {
        skipped.push({ email: user.email, reason: "already-sent", dayNumber });
        await recordMailEvent(context.env, {
          runId,
          email: user.email,
          canon,
          dayNumber,
          eventType: "skipped",
          detail: "already-sent",
        });
        continue;
      }

      try {
        const reading = await loadReading(context, canon, dayNumber);
        const subject = buildDevotionalSubject(dayNumber);
        const unsubscribeUrl = await buildUnsubscribeUrl(context, user.email);
        const html = renderDevotionalEmail({
          site: data.site || {},
          user,
          reading,
          unsubscribeUrl,
        });

        if (!dryRun && context.env.RESEND_API_KEY) {
          await sendViaResend(context, { to: user.email, subject, html });
        }

        if (!explicitDryRun) {
          await context.env.SITE_DB.prepare(
            `
              UPDATE bible_users
              SET last_sent_day = ?, last_sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
              WHERE email = ?
            `
          )
            .bind(dayNumber, user.email)
            .run();
        }

        sent.push({
          email: user.email,
          canon,
          dayNumber,
          mode: dryRun ? "dry-run" : "sent",
        });

        await recordMailEvent(context.env, {
          runId,
          email: user.email,
          canon,
          dayNumber,
          eventType: dryRun ? "dry-run" : "sent",
          detail: subject,
        });
      } catch (error) {
        failed.push({
          email: user.email,
          canon,
          dayNumber,
          error: error instanceof Error ? error.message : "send failed",
        });

        await recordMailEvent(context.env, {
          runId,
          email: user.email,
          canon,
          dayNumber,
          eventType: "failed",
          detail: error instanceof Error ? error.message : "send failed",
        });
      }
    }

    await finishMailRun(context.env, {
      runId,
      sentCount: sent.length,
      skippedCount: skipped.length,
      failedCount: failed.length,
      status: failed.length ? "complete-with-errors" : "complete",
      note: dryRun ? "dry-run batch" : "batch sent",
    });

    return Response.json(
      {
        ok: true,
        runId,
        generatedAt: data.generated_at || null,
        sent,
        skipped,
        failed,
        dryRun,
      },
      {
        headers: {
          "cache-control": "no-store",
        },
      }
    );
  } catch (error) {
    if (context.env.SITE_DB && runId) {
      try {
        await finishMailRun(context.env, {
          runId,
          status: "failed",
          note: error instanceof Error ? error.message : "batch failed before completion",
        });
      } catch (_) {
        // Leave the main failure path intact if the audit trail cannot be written.
      }
    }

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
