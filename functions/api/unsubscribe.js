import { verifyUnsubscribeToken } from "../_lib/unsubscribe.js";

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const email = String(url.searchParams.get("email") || "").trim().toLowerCase();
  const token = String(url.searchParams.get("token") || "");

  if (!email || !token) {
    return htmlResponse("This unsubscribe link is incomplete.", 400);
  }

  if (!context.env.SITE_DB) {
    return htmlResponse("Email preferences are temporarily unavailable.", 500);
  }

  const valid = await verifyUnsubscribeToken(context, email, token);
  if (!valid) {
    return htmlResponse("This unsubscribe link is invalid or expired.", 403);
  }

  await context.env.SITE_DB.prepare(
    `
      UPDATE bible_users
      SET subscribed = 0, updated_at = CURRENT_TIMESTAMP
      WHERE email = ?
    `
  )
    .bind(email)
    .run();

  return htmlResponse(
    "You are unsubscribed. Shadowfetch will stop sending the daily Bible email to this address.",
    200
  );
}

function htmlResponse(message, status) {
  return new Response(
    `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shadowfetch Bible Edition</title>
    <style>
      body { margin: 0; background: #15120f; color: #f5f0e8; font-family: Georgia, serif; }
      main { max-width: 42rem; margin: 0 auto; padding: 4rem 1.25rem; }
      .card { background: #241d18; border: 1px solid rgba(184,141,74,.25); padding: 2rem; }
      h1 { margin: 0 0 1rem; font-size: 2rem; }
      p { line-height: 1.7; color: #d7c8b5; }
      a { color: #f5f0e8; }
    </style>
  </head>
  <body>
    <main>
      <section class="card">
        <h1>Shadowfetch • Bible Edition</h1>
        <p>${message}</p>
        <p><a href="https://www.shadowfetch.com/">Return to the site</a></p>
      </section>
    </main>
  </body>
</html>`,
    {
      status,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
      },
    }
  );
}
