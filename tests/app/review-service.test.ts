import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createDb } from "../../src/infra/db/client.js";
import { DocumentRepo } from "../../src/infra/db/document-repo.js";
import { EntryRepo } from "../../src/infra/db/entry-repo.js";
import { AuditRepo } from "../../src/infra/db/audit-repo.js";
import { AuditService } from "../../src/app/audit-service.js";
import { ReviewService } from "../../src/app/review-service.js";
import type { NormalizedEntry } from "../../src/domain/schemas.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

function setup() {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `review-${dbPathCounter++}.sqlite`);
  const db = createDb(dbPath);
  db.exec(fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8"));
  return { db };
}

function seedEntry(entryRepo: EntryRepo, documentRepo: DocumentRepo): NormalizedEntry {
  const now = "2026-04-17T00:00:00+00:00";
  const source = documentRepo.insert({
    documentId: "doc_1",
    sourceType: "bank_statement",
    filename: "bank.csv",
    mimeType: "text/csv",
    importedAt: now
  });
  const entry: NormalizedEntry = {
    entryId: "entry_1",
    sourceDocument: source,
    amount: 100,
    currency: "USD",
    categoryDecision: {
      suggestedCategory: "shopping",
      confidence: 0.5,
      source: "rule"
    },
    duplicateCheck: {
      status: "near_duplicate_suspected",
      confidence: 0.8,
      signals: ["same_amount"]
    },
    status: "needs_review",
    reviewReasons: ["duplicate_suspected"],
    extractionMeta: {
      extractorVersion: "v1",
      confidence: 0.5,
      warnings: []
    },
    lineItems: [],
    createdAt: now,
    updatedAt: now,
    transactionDate: "2026-04-16"
  };
  entryRepo.upsert(entry);
  return entry;
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("review-") && file.endsWith(".sqlite")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("ReviewService", () => {
  it("supports approve and category edit operations", () => {
    const { db } = setup();
    const documentRepo = new DocumentRepo(db);
    const entryRepo = new EntryRepo(db);
    seedEntry(entryRepo, documentRepo);
    const service = new ReviewService(entryRepo, new AuditService(new AuditRepo(db)));

    const approved = service.approveEntry("entry_1");
    expect(approved.status).toBe("approved");

    const edited = service.editCategory("entry_1", "transport");
    expect(edited.categoryDecision.finalCategory).toBe("transport");
    db.close();
  });
});
