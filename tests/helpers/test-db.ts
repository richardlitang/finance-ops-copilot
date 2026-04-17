import fs from "node:fs";
import path from "node:path";
import type Database from "better-sqlite3";
import { createDb } from "../../src/infra/db/client.js";
import { runMigrations } from "../../src/infra/db/migrate.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

export function createMigratedTestDatabase(prefix: string): { db: Database.Database; dbPath: string } {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `${prefix}-${dbPathCounter++}.sqlite`);
  runMigrations({ dbPath });
  const db = createDb(dbPath);
  return { db, dbPath };
}

export function cleanupTempDatabases(prefix: string): void {
  if (!fs.existsSync(tmpDir)) {
    return;
  }

  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith(`${prefix}-`) && (file.endsWith(".sqlite") || file.endsWith(".sqlite-wal") || file.endsWith(".sqlite-shm"))) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
}
