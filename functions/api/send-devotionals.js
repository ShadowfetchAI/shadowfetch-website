import {
  computeDayNumber,
  loadBibleEdition,
  loadReading,
  normalizeCanon,
} from "../_lib/bible.js";

function renderEmailHtml({ site, user, reading }) {
  const chapters = Array.isArray(reading?.chapters) ? reading.chapters : [];
  const chapterMarkup = chapters
    .map((chapter) => {
      const verses = (chapter.verses || [])
        .map(
          (verse) =>
            `<p style="margin:0 0 10px;line-height:1.7;"><sup style="font-size:0.72rem;color:#8a5d24;">${verse.verse}</sup> ${escapeHtml(verse.text)}</p>`
        )
        .join("");
      return `
        <section style="border:1px solid #d0c3b0;background:#fbf8f3;padding:18px 18px 10px;margin:0 0 18px;">
          <p style="margin:0 0 6px;font:600 12px/1.3 'IBM Plex Sans',Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#7b654d;">Chapter</p>
          <h3 style="margin:0 0 8px;font:600 28px/1.1 Georgia,serif;color:#241b16;">${escapeHtml(chapter.chapter_title)}</h3>
          ${verses}
        </section>
      `;
    })
    .join("");

  return `<!DOCTYPE html>
  <html lang="en">
    <body style="margin:0;background:#15120f;color:#241b16;">
      <div style="max-width:760px;margin:0 auto;background:#f7f2ea;padding:28px 24px 40px;">
        <p style="margin:0 0 6px;font:600 12px/1.3 'IBM Plex Sans',Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#8a5d24;">Shadowfetch • Bible Edition</p>
        <h1 style="margin:0 0 8px;font:600 42px/1.05 Georgia,serif;color:#241b16;">Today’s Reading – Day ${reading.day_number}</h1>
        <p style="margin:0 0 16px;font:400 18px/1.5 Georgia,serif;color:#5d4f44;">${escapeHtml(reading.references)}</p>
        <p style="margin:0 0 24px;font:400 16px/1.7 Georgia,serif;color:#6d5d52;">Fetch the Word. Abide in the Shadow.</p>
        ${chapterMarkup}
        <p style="margin:24px 0 12px;font:400 16px/1.7 Georgia,serif;color:#5d4f44;">These daily chapters are free thanks to people like you. Donate what you want to help keep the emails going for everyone.</p>
        <p style="margin:0 0 16px;"><a href="${site.support_url}" style="display:inline-block;padding:12px 18px;background:#8a5d24;color:#fff7ed;text-decoration:none;font:600 14px/1 'IBM Plex Sans',Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;">Buy Me a Coffee</a></p>
        <p style="margin:0;font:400 13px/1.6 'IBM Plex Sans',Arial,sans-serif;color:#7b654d;">This message was prepared for ${escapeHtml(user.email)}. You can update your reading preferences anytime at https://www.shadowfetch.com/settings/.</p>
      </div>
    </body>
  </html>`;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function sendViaResend(context, { to, subject, html }) {
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${context.env.RESEND_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: context.env.RESEND_FROM || "Shadowfetch Bible <hello@shadowfetch.com>",
      to: [to],
      subject,
      html,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Resend error ${response.status}: ${text}`);
  }

  return response.json();
}

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

    for (const user of results || []) {
      const canon = normalizeCanon(user.canon);
      const dayNumber = computeDayNumber(user.start_date);
      if (Number(user.last_sent_day || 0) === dayNumber) {
        skipped.push({ email: user.email, reason: "already-sent", dayNumber });
        continue;
      }

      const reading = await loadReading(context, canon, dayNumber);
      const subject = `Shadowfetch • Bible Edition — Day ${dayNumber}`;
      const html = renderEmailHtml({
        site: data.site || {},
        user,
        reading,
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
