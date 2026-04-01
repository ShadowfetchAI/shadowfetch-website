const SITE_SCHEMA_STATEMENTS = [
  `CREATE TABLE IF NOT EXISTS site_metrics (
    key TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `INSERT OR IGNORE INTO site_metrics (key, value, updated_at)
    VALUES ('site_visits', 0, CURRENT_TIMESTAMP)`,
  `CREATE TABLE IF NOT EXISTS bible_users (
    email TEXT PRIMARY KEY,
    canon TEXT NOT NULL DEFAULT 'protestant',
    start_date TEXT NOT NULL,
    subscribed INTEGER NOT NULL DEFAULT 1,
    last_sent_day INTEGER,
    last_sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS bible_progress (
    email TEXT NOT NULL,
    reading_day INTEGER NOT NULL,
    reading_date TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (email, reading_day),
    FOREIGN KEY (email) REFERENCES bible_users(email) ON DELETE CASCADE
  )`,
  `CREATE INDEX IF NOT EXISTS idx_bible_progress_date ON bible_progress(reading_date)`,
  `CREATE TABLE IF NOT EXISTS bible_mail_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    requested_at TEXT,
    sent_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    dry_run INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',
    note TEXT
  )`,
  `CREATE INDEX IF NOT EXISTS idx_bible_mail_runs_started_at ON bible_mail_runs(started_at DESC)`,
  `CREATE TABLE IF NOT EXISTS bible_mail_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    email TEXT NOT NULL,
    canon TEXT,
    day_number INTEGER,
    event_type TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES bible_mail_runs(id) ON DELETE SET NULL
  )`,
  `CREATE INDEX IF NOT EXISTS idx_bible_mail_events_run_id ON bible_mail_events(run_id)`,
  `CREATE INDEX IF NOT EXISTS idx_bible_mail_events_email ON bible_mail_events(email)`,
];

let schemaReadyPromise = null;

export async function ensureSiteSchema(env) {
  if (!env?.SITE_DB) {
    throw new Error("Database binding is missing.");
  }

  if (!schemaReadyPromise) {
    schemaReadyPromise = (async () => {
      for (const statement of SITE_SCHEMA_STATEMENTS) {
        await env.SITE_DB.prepare(statement).run();
      }
    })().catch((error) => {
      schemaReadyPromise = null;
      throw error;
    });
  }

  await schemaReadyPromise;
}

export async function openMailRun(env, { requestedAt = null, dryRun = false, note = null } = {}) {
  await ensureSiteSchema(env);
  const runId = crypto.randomUUID();
  await env.SITE_DB.prepare(
    `
      INSERT INTO bible_mail_runs (id, requested_at, dry_run, status, note)
      VALUES (?, ?, ?, 'running', ?)
    `
  )
    .bind(runId, requestedAt, dryRun ? 1 : 0, note)
    .run();
  return runId;
}

export async function recordMailEvent(
  env,
  { runId = null, email, canon = null, dayNumber = null, eventType, detail = null }
) {
  if (!email || !eventType) {
    return;
  }

  await ensureSiteSchema(env);
  await env.SITE_DB.prepare(
    `
      INSERT INTO bible_mail_events (run_id, email, canon, day_number, event_type, detail)
      VALUES (?, ?, ?, ?, ?, ?)
    `
  )
    .bind(runId, email, canon, dayNumber, eventType, detail)
    .run();
}

export async function finishMailRun(
  env,
  { runId, sentCount = 0, skippedCount = 0, failedCount = 0, status = "complete", note = null }
) {
  if (!runId) {
    return;
  }

  await ensureSiteSchema(env);
  await env.SITE_DB.prepare(
    `
      UPDATE bible_mail_runs
      SET
        finished_at = CURRENT_TIMESTAMP,
        sent_count = ?,
        skipped_count = ?,
        failed_count = ?,
        status = ?,
        note = ?
      WHERE id = ?
    `
  )
    .bind(sentCount, skippedCount, failedCount, status, note, runId)
    .run();
}
