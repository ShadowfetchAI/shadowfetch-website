function normalizeEmail(value) {
  return String(value || "").trim().toLowerCase();
}

function getSecret(env) {
  return String(env.UNSUBSCRIBE_SECRET || env.CRON_SECRET || env.SITE_NAME || "shadowfetch-bible");
}

function base64Url(bytes) {
  let binary = "";
  const chunk = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  for (let index = 0; index < chunk.length; index += 1) {
    binary += String.fromCharCode(chunk[index]);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function signEmail(email, env) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(getSecret(env)),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(normalizeEmail(email)));
  return base64Url(signature);
}

export async function buildUnsubscribeUrl(context, email) {
  const safeEmail = normalizeEmail(email);
  const token = await signEmail(safeEmail, context.env);
  const base = context.env.SITE_ORIGIN || new URL(context.request.url).origin;
  const url = new URL("/api/unsubscribe", base);
  url.searchParams.set("email", safeEmail);
  url.searchParams.set("token", token);
  return url.toString();
}

export async function verifyUnsubscribeToken(context, email, token) {
  if (!email || !token) {
    return false;
  }
  const expected = await signEmail(email, context.env);
  return expected === String(token);
}
