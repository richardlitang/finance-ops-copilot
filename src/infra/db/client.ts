import Database from "better-sqlite3";
import path from "node:path";
import fs from "node:fs";

export function resolveDbPath(): string {
  const envPath = process.env.DB_PATH;
  if (envPath && envPath.trim() !== "") {
    return path.resolve(envPath);
  }
  return path.resolve(".tmp/finance_ops.sqlite");
}

export function createDb(dbPath = resolveDbPath()): Database.Database {
  const parentDir = path.dirname(dbPath);
  fs.mkdirSync(parentDir, { recursive: true });
  const db = new Database(dbPath);
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");
  return db;
}
