import type Database from "better-sqlite3";

export class FingerprintRepo {
  constructor(private readonly db: Database.Database) {}

  upsert(fingerprint: string, entryId: string, createdAt: string): void {
    this.db
      .prepare(
        `INSERT INTO import_fingerprints (fingerprint, entry_id, created_at)
         VALUES (?, ?, ?)
         ON CONFLICT(fingerprint) DO UPDATE SET
         entry_id = excluded.entry_id`
      )
      .run(fingerprint, entryId, createdAt);
  }

  findEntryIdByFingerprint(fingerprint: string): string | null {
    const row = this.db
      .prepare("SELECT entry_id FROM import_fingerprints WHERE fingerprint = ?")
      .get(fingerprint) as { entry_id: string } | undefined;
    return row?.entry_id ?? null;
  }

  asMap(): Map<string, string> {
    const rows = this.db.prepare("SELECT fingerprint, entry_id FROM import_fingerprints").all() as Array<{
      fingerprint: string;
      entry_id: string;
    }>;
    return new Map(rows.map((row) => [row.fingerprint, row.entry_id]));
  }
}
