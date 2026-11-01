-- AGENT CITY v0.1. Run once using: npx wrangler d1 execute agent-city --remote --file=./schema.sql
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
INSERT OR IGNORE INTO settings (key,value) VALUES ('autopilot','0');

CREATE TABLE IF NOT EXISTS missions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  goal TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','completed')),
  current_agent INTEGER NOT NULL DEFAULT 1 CHECK(current_agent BETWEEN 1 AND 5),
  turns INTEGER NOT NULL DEFAULT 0,
  max_turns INTEGER NOT NULL DEFAULT 20,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  lease_until TEXT,
  error_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status,id);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id INTEGER REFERENCES missions(id),
  author INTEGER NOT NULL CHECK(author BETWEEN 0 AND 5),
  to_agent INTEGER CHECK(to_agent BETWEEN 1 AND 5),
  reply_to INTEGER REFERENCES messages(id),
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_mission ON messages(mission_id,id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
