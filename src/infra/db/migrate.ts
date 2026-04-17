import fs from "node:fs";
import path from "node:path";
import { createDb } from "./client.js";

function runMigrations(): void {
  const db = createDb();
  const migrationsDir = path.resolve("src/infra/db/migrations");
  const files = fs
    .readdirSync(migrationsDir)
    .filter((name) => name.endsWith(".sql"))
    .sort();

  db.exec(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT NOT NULL UNIQUE,
      applied_at TEXT NOT NULL
    );
  `);

  const alreadyAppliedRows = db.prepare("SELECT filename FROM schema_migrations").all() as Array<{
    filename: string;
  }>;
  const alreadyApplied = new Set(alreadyAppliedRows.map((row) => row.filename));

  for (const file of files) {
    if (alreadyApplied.has(file)) {
      continue;
    }
    const sql = fs.readFileSync(path.join(migrationsDir, file), "utf8");
    db.exec(sql);
    db.prepare("INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)").run(
      file,
      new Date().toISOString()
    );
  }

  db.close();
}

runMigrations();
