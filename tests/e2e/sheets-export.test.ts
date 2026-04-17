import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createDb } from "../../src/infra/db/client.js";
import { DocumentRepo } from "../../src/infra/db/document-repo.js";
import { EntryRepo } from "../../src/infra/db/entry-repo.js";
import { GoogleSheetsService, type SheetsGateway } from "../../src/adapters/sheets/google-sheets-service.js";
import type { NormalizedEntry } from "../../src/domain/schemas.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

class InMemoryGateway implements SheetsGateway {
  writes: Array<{ tab: string; rows: Array<Record<string, unknown>>; keyField: string }> = [];
  async upsertRows(tab: string, rows: Array<Record<string, unknown>>, keyField: string): Promise<void> {
    this.writes.push({ tab, rows, keyField });
  }
}

function setup() {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `e2e-sheets-${dbPathCounter++}.sqlite`);
  const db = createDb(dbPath);
  db.exec(fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8"));
  return { db, entryRepo: new EntryRepo(db), documentRepo: new DocumentRepo(db) };
}

function seedEntry(
  entryRepo: EntryRepo,
  documentRepo: DocumentRepo,
  entryId: string,
  status: NormalizedEntry["status"],
  duplicateStatus: NormalizedEntry["duplicateCheck"]["status"]
): void {
  const now = "2026-04-17T00:00:00+00:00";
  const docId = `doc-${entryId}`;
  documentRepo.insert({
    documentId: docId,
    sourceType: "bank_statement",
    filename: `${docId}.csv`,
    mimeType: "text/csv",
    importedAt: now
  });
  entryRepo.upsert({
    entryId,
    sourceDocument: {
      documentId: docId,
      sourceType: "bank_statement",
      filename: `${docId}.csv`,
      mimeType: "text/csv",
      importedAt: now
    },
    merchantRaw: "MERCHANT",
    merchantNormalized: "merchant",
    transactionDate: "2026-04-16",
    amount: 100,
    currency: "USD",
    categoryDecision: {
      suggestedCategory: "shopping",
      finalCategory: "shopping",
      confidence: 0.9,
      source: "rule"
    },
    duplicateCheck: {
      status: duplicateStatus,
      confidence: duplicateStatus === "none" ? 0.1 : 1,
      signals: []
    },
    status,
    reviewReasons: status === "needs_review" ? ["duplicate_suspected"] : [],
    extractionMeta: {
      extractorVersion: "v1",
      confidence: 0.9,
      warnings: []
    },
    lineItems: [],
    createdAt: now,
    updatedAt: now
  });
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("e2e-sheets-") && file.endsWith(".sqlite")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("E2E sheets export contract", () => {
  it("exports approved rows, excludes exact duplicates, and keeps review queue isolated", async () => {
    const { db, entryRepo, documentRepo } = setup();
    seedEntry(entryRepo, documentRepo, "approved_a", "approved", "none");
    seedEntry(entryRepo, documentRepo, "approved_dup", "needs_review", "exact_duplicate_import");
    seedEntry(entryRepo, documentRepo, "review_a", "needs_review", "near_duplicate_suspected");

    const entries = entryRepo.listAll();
    const gateway = new InMemoryGateway();
    const sheets = new GoogleSheetsService(gateway);

    const approvedCount = await sheets.syncApprovedEntries(entries, "2026-04-17T00:00:00+00:00");
    const reviewCount = await sheets.syncReviewQueue(entries);

    expect(approvedCount).toBe(1);
    expect(reviewCount).toBe(2);

    const normalizedWrite = gateway.writes.find((write) => write.tab === "normalized_entries");
    const reviewWrite = gateway.writes.find((write) => write.tab === "review_queue");
    expect(normalizedWrite?.rows).toHaveLength(1);
    expect(reviewWrite?.rows).toHaveLength(2);
    expect(normalizedWrite?.rows[0]?.entry_id).toBe("approved_a");
    const reviewIds = new Set((reviewWrite?.rows ?? []).map((row) => String(row.entry_id)));
    expect(reviewIds.has("review_a")).toBe(true);
    expect(reviewIds.has("approved_dup")).toBe(true);

    db.close();
  });
});
