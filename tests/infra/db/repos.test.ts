import { afterEach, describe, expect, it } from "vitest";
import { DocumentRepo } from "../../../src/infra/db/document-repo.js";
import { EntryRepo } from "../../../src/infra/db/entry-repo.js";
import { MappingRuleRepo } from "../../../src/infra/db/mapping-rule-repo.js";
import { AuditRepo } from "../../../src/infra/db/audit-repo.js";
import { ExtractedCandidateRepo } from "../../../src/infra/db/extracted-candidate-repo.js";
import { cleanupTempDatabases, createMigratedTestDatabase } from "../../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("test");
});

describe("db repositories", () => {
  it("persists and fetches source documents", () => {
    const { db } = createMigratedTestDatabase("test");
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
    const { db } = createMigratedTestDatabase("test");
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
    const { db } = createMigratedTestDatabase("test");
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

  it("persists extracted candidates linked to documents and entries", () => {
    const { db } = createMigratedTestDatabase("test");
    const documentRepo = new DocumentRepo(db);
    const entryRepo = new EntryRepo(db);
    const repo = new ExtractedCandidateRepo(db);
    const sourceDocument = documentRepo.insert({
      documentId: "doc_1",
      sourceType: "receipt",
      filename: "receipt.txt",
      mimeType: "text/plain",
      importedAt: "2026-04-17T00:00:00+00:00"
    });
    entryRepo.upsert({
      entryId: "entry_1",
      sourceDocument,
      merchantRaw: "ALDI",
      merchantNormalized: "aldi",
      amount: 42.97,
      currency: "EUR",
      categoryDecision: {
        suggestedCategory: "groceries",
        confidence: 0.8,
        source: "rule",
        finalCategory: "groceries"
      },
      duplicateCheck: {
        status: "none",
        confidence: 0.1,
        signals: []
      },
      status: "approved",
      reviewReasons: [],
      extractionMeta: {
        extractorVersion: "v1",
        confidence: 0.82,
        warnings: []
      },
      lineItems: [],
      createdAt: "2026-04-17T00:00:00+00:00",
      updatedAt: "2026-04-17T00:00:00+00:00"
    });

    repo.insert({
      candidateId: "cand_1",
      documentId: "doc_1",
      sourceType: "receipt",
      entryId: "entry_1",
      merchantRaw: "ALDI",
      amountRaw: "42,97",
      currencyRaw: "EUR",
      confidence: 0.82,
      warnings: ["uncertain_category"],
      rawText: "ALDI\nTOTAL 42,97 EUR",
      extractorVersion: "v1",
      lineItems: [],
      createdAt: "2026-04-17T00:00:00+00:00"
    });

    const byDocument = repo.listByDocumentId("doc_1");
    const byEntry = repo.listByEntryId("entry_1");
    expect(byDocument).toHaveLength(1);
    expect(byEntry).toHaveLength(1);
    expect(byDocument[0]?.merchantRaw).toBe("ALDI");
    db.close();
  });
});
