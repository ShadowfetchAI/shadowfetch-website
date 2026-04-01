import { normalizeStartDate, todayIsoString, validateEmail } from "../_lib/bible.js";
import { ensureSiteSchema } from "../_lib/db.js";

export async function onRequestGet(context) {
  try {
    const url = new URL(context.request.url);
    const email = validateEmail(url.searchParams.get("email"));
    const startDate = normalizeStartDate(url.searchParams.get("start_date"));

    if (!context.env.SITE_DB || !email) {
      return Response.json(
        {
          ok: true,
          email: email || null,
          startDate,
          items: [],
        },
        {
          headers: {
            "cache-control": "no-store",
          },
        }
      );
    }

    await ensureSiteSchema(context.env);

    let results = [];
    try {
      const query = await context.env.SITE_DB.prepare(
        `
          SELECT reading_day, reading_date, completed_at
          FROM bible_progress
          WHERE email = ?
          ORDER BY reading_day ASC
        `
      )
        .bind(email)
        .all();
      results = Array.isArray(query.results) ? query.results : [];
    } catch (_) {
      results = [];
    }

    return Response.json(
      {
        ok: true,
        email,
        startDate,
        items: results,
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
        error: "Could not load reading progress.",
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

export async function onRequestPost(context) {
  try {
    const payload = await context.request.json();
    const email = validateEmail(payload?.email);
    const readingDay = Number.parseInt(String(payload?.reading_day || "1"), 10) || 1;
    const readingDate = String(payload?.reading_date || todayIsoString());

    let storageMode = "local-only";
    if (context.env.SITE_DB && email) {
      try {
        await ensureSiteSchema(context.env);
        await context.env.SITE_DB.prepare(
          `
            INSERT INTO bible_progress (email, reading_day, reading_date, completed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(email, reading_day) DO UPDATE SET
              reading_date = excluded.reading_date,
              completed_at = CURRENT_TIMESTAMP
          `
        )
          .bind(email, readingDay, readingDate)
          .run();
        storageMode = "database";
      } catch (_) {
        storageMode = "local-only";
      }
    }

    return Response.json(
      {
        ok: true,
        readingDay,
        readingDate,
        email: email || null,
        storageMode,
        message: "Marked as read.",
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
        error: "Could not save reading progress.",
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
