CREATE TABLE IF NOT EXISTS bible_users (
  email TEXT PRIMARY KEY,
  canon TEXT NOT NULL DEFAULT 'protestant',
  start_date TEXT NOT NULL,
  subscribed INTEGER NOT NULL DEFAULT 1,
  last_sent_day INTEGER,
  last_sent_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bible_progress (
  email TEXT NOT NULL,
  reading_day INTEGER NOT NULL,
  reading_date TEXT NOT NULL,
  completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (email, reading_day),
  FOREIGN KEY (email) REFERENCES bible_users(email) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bible_progress_date ON bible_progress(reading_date);
