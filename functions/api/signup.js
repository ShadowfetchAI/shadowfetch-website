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
import { ensureSiteSchema, recordMailEvent } from "../_lib/db.js";
import { buildUnsubscribeUrl } from "../_lib/unsubscribe.js";

export async function onRequestPost(context) {
  try {
    const payload = await context.request.json();
    const email = validateEmail(payload?.email);
    const canon = normalizeCanon(payload?.canon);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const defaultStartDate = tomorrow.toISOString().slice(0, 10);
    const startDate = normalizeStartDate(payload?.start_date || defaultStartDate);
    const subscribed = payload?.subscribed === false || payload?.subscribed === "0" ? 0 : 1;

    if (!email) {
      return Response.json({ ok: false, error: "A valid email address is required." }, { status: 400 });
    }

    let welcomeEmail = "not-sent";
    if (!context.env.SITE_DB) {
      return Response.json(
        {
          ok: false,
          error: "Subscriptions are temporarily unavailable. Please try again in a little while.",
        },
        {
          status: 503,
          headers: {
            "cache-control": "no-store",
          },
        }
      );
    }

    await ensureSiteSchema(context.env);
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

        await context.env.SITE_DB.prepare(
          `
            UPDATE bible_users
            SET last_sent_day = ?, last_sent_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
          `
        )
          .bind(dayNumber, email)
          .run();

        await recordMailEvent(context.env, {
          email,
          canon,
          dayNumber,
          eventType: context.env.RESEND_API_KEY ? "welcome-sent" : "welcome-dry-run",
          detail: subject,
        });
      } catch (error) {
        welcomeEmail = "failed";
        await recordMailEvent(context.env, {
          email,
          canon,
          dayNumber,
          eventType: "welcome-failed",
          detail: error instanceof Error ? error.message : "welcome send failed",
        });
      }
    }

    return Response.json(
      {
        ok: true,
        email,
        canon,
        startDate,
        subscribed: Boolean(subscribed),
        storageMode: "database",
        dayNumber,
        welcomeEmail,
        redirect: "/blessed/",
        message:
          welcomeEmail === "sent"
            ? "Your first reading is already on its way. Have a blessed day."
            : "Your first reading will be delivered to your inbox tomorrow. Have a blessed day.",
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
