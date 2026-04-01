import { ensureSiteSchema } from "./db.js";

const DEFAULT_NAMESPACE = "shadowfetch-news";
const DEFAULT_COUNTER_KEY = "site_visits";
const COUNTERAPI_BASE = "https://api.counterapi.dev/v1";

export async function readCounter(env) {
  const d1Result = await readCounterFromD1(env);
  if (d1Result) {
    return d1Result;
  }

  return readCounterFromCounterApi(env);
}

export async function incrementCounter(env) {
  const d1Result = await incrementCounterInD1(env);
  if (d1Result) {
    return d1Result;
  }

  return incrementCounterViaCounterApi(env);
}

async function readCounterFromD1(env) {
  if (!env.SITE_DB) {
    return null;
  }

  try {
    await ensureSiteSchema(env);
    const row = await env.SITE_DB
      .prepare("SELECT value, updated_at FROM site_metrics WHERE key = ?")
      .bind(counterKey(env))
      .first();

    if (!row) {
      return {
        configured: true,
        backend: "d1",
        count: 0,
        updatedAt: null
      };
    }

    return {
      configured: true,
      backend: "d1",
      count: Number(row.value || 0),
      updatedAt: row.updated_at || null
    };
  } catch (error) {
    return null;
  }
}

async function incrementCounterInD1(env) {
  if (!env.SITE_DB) {
    return null;
  }

  try {
    await ensureSiteSchema(env);
    await env.SITE_DB
      .prepare(
        "INSERT INTO site_metrics (key, value, updated_at) VALUES (?, 0, CURRENT_TIMESTAMP) " +
        "ON CONFLICT(key) DO NOTHING"
      )
      .bind(counterKey(env))
      .run();

    await env.SITE_DB
      .prepare(
        "UPDATE site_metrics SET value = value + 1, updated_at = CURRENT_TIMESTAMP WHERE key = ?"
      )
      .bind(counterKey(env))
      .run();

    return readCounterFromD1(env);
  } catch (error) {
    return null;
  }
}

async function readCounterFromCounterApi(env) {
  const endpoint = `${COUNTERAPI_BASE}/${counterNamespace(env)}/${counterName(env)}/`;
  const response = await fetch(endpoint, { cf: { cacheTtl: 0, cacheEverything: false } });
  if (!response.ok) {
    throw new Error(`Counter API read failed with ${response.status}`);
  }

  const payload = await response.json();
  return {
    configured: true,
    backend: "counterapi",
    count: Number(payload.count ?? payload.value ?? 0),
    updatedAt: new Date().toISOString()
  };
}

async function incrementCounterViaCounterApi(env) {
  const endpoint = `${COUNTERAPI_BASE}/${counterNamespace(env)}/${counterName(env)}/up`;
  const response = await fetch(endpoint, { cf: { cacheTtl: 0, cacheEverything: false } });
  if (!response.ok) {
    throw new Error(`Counter API increment failed with ${response.status}`);
  }

  const payload = await response.json();
  return {
    configured: true,
    backend: "counterapi",
    count: Number(payload.count ?? payload.value ?? 0),
    updatedAt: new Date().toISOString()
  };
}

function counterNamespace(env) {
  return String(env.COUNTER_NAMESPACE || DEFAULT_NAMESPACE);
}

function counterName(env) {
  return String(env.COUNTER_NAME || "site-visits");
}

function counterKey(env) {
  return String(env.COUNTER_KEY || DEFAULT_COUNTER_KEY);
}
