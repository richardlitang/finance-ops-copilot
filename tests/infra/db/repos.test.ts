import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createDb } from "../../../src/infra/db/client.js";
import { DocumentRepo } from "../../../src/infra/db/document-repo.js";
import { MappingRuleRepo } from "../../../src/infra/db/mapping-rule-repo.js";
import { AuditRepo } from "../../../src/infra/db/audit-repo.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

function createTestDatabase() {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `test-${dbPathCounter++}.sqlite`);
  const db = createDb(dbPath);
  const schemaSql = fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8");
  db.exec(schemaSql);
  return { db, dbPath };
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("test-") && file.endsWith(".sqlite")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("db repositories", () => {
  it("persists and fetches source documents", () => {
    const { db } = createTestDatabase();
    const repo = new DocumentRepo(db);
    const inserted = repo.insert({
      documentId: "doc_1",
      sourceType: "receipt",
      filename: "receipt.jpg",
      mimeType: "image/jpeg",
      importedAt: "2026-04-17T00:00:00+00:00"
    });

    const found = repo.findById("doc_1");
    expect(found).toEqual(inserted);
    db.close();
  });

  it("upserts and lists mapping rules", () => {
    const { db } = createTestDatabase();
    const repo = new MappingRuleRepo(db);
    repo.upsert({
      ruleId: "rule_1",
      field: "merchant",
      pattern: "GRAB",
      targetCategory: "transport",
      priority: 10,
      createdBy: "system",
      createdAt: "2026-04-17T00:00:00+00:00"
    });

    const rules = repo.list();
    expect(rules).toHaveLength(1);
    expect(rules[0]?.targetCategory).toBe("transport");
    db.close();
  });

  it("persists and returns audit events", () => {
    const { db } = createTestDatabase();
    const repo = new AuditRepo(db);
    repo.insert({
      eventId: "evt_1",
      entryId: "entry_1",
      eventType: "entry_normalized",
      eventAt: "2026-04-17T00:00:00+00:00",
      actor: "system",
      payloadJson: "{\"ok\":true}"
    });

    const events = repo.listByEntryId("entry_1");
    expect(events).toHaveLength(1);
    expect(events[0]?.eventId).toBe("evt_1");
    db.close();
  });
});
