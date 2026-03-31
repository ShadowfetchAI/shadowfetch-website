import {
  computeDayNumber,
  loadBibleEdition,
  loadReading,
  normalizeCanon,
  normalizeStartDate,
  selectPlan,
  validateEmail,
} from "../_lib/bible.js";
import {
  buildDevotionalSubject,
  renderDevotionalEmail,
  sendViaResend,
} from "../_lib/devotional-email.js";
import { buildUnsubscribeUrl } from "../_lib/unsubscribe.js";

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
    let welcomeEmail = "not-sent";
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
    const todayIso = new Date().toISOString().slice(0, 10);

    if (subscribed && startDate <= todayIso) {
      try {
        const reading = await loadReading(context, canon, dayNumber);
        const subject = buildDevotionalSubject(dayNumber);
        const unsubscribeUrl = await buildUnsubscribeUrl(context, email);
        const html = renderDevotionalEmail({
          site: data.site || {},
          user: { email },
          reading,
          unsubscribeUrl,
        });

        if (context.env.RESEND_API_KEY) {
          await sendViaResend(context, { to: email, subject, html });
          welcomeEmail = "sent";
        } else {
          welcomeEmail = "dry-run";
        }

        if (storageMode === "database") {
          await context.env.SITE_DB.prepare(
            `
              UPDATE bible_users
              SET last_sent_day = ?, last_sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
              WHERE email = ?
            `
          )
            .bind(dayNumber, email)
            .run();
        }
      } catch (_) {
        welcomeEmail = "failed";
      }
    }

    return Response.json(
      {
        ok: true,
        email,
        canon,
        startDate,
        subscribed: Boolean(subscribed),
        storageMode,
        dayNumber,
        welcomeEmail,
        redirect: `/bible/?canon=${encodeURIComponent(canon)}&start_date=${encodeURIComponent(startDate)}`,
        message:
          welcomeEmail === "sent"
            ? "Your reading desk is ready. Day 1 is already on its way to your inbox."
            : "Your reading desk is ready. Today's chapters are waiting for you.",
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
