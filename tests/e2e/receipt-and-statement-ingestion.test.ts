import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createDb } from "../../src/infra/db/client.js";
import { DocumentRepo } from "../../src/infra/db/document-repo.js";
import { EntryRepo } from "../../src/infra/db/entry-repo.js";
import { MappingRuleRepo } from "../../src/infra/db/mapping-rule-repo.js";
import { AuditRepo } from "../../src/infra/db/audit-repo.js";
import { FingerprintRepo } from "../../src/infra/db/fingerprint-repo.js";
import { IntakeService } from "../../src/app/intake-service.js";
import { AuditService } from "../../src/app/audit-service.js";
import { ImportPipeline } from "../../src/app/import-pipeline.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

function setup() {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `e2e-ingest-${dbPathCounter++}.sqlite`);
  const db = createDb(dbPath);
  db.exec(fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8"));

  const repos = {
    documentRepo: new DocumentRepo(db),
    entryRepo: new EntryRepo(db),
    mappingRuleRepo: new MappingRuleRepo(db),
    auditRepo: new AuditRepo(db),
    fingerprintRepo: new FingerprintRepo(db)
  };
  const services = {
    intakeService: new IntakeService(repos.documentRepo),
    auditService: new AuditService(repos.auditRepo)
  };
  const pipeline = new ImportPipeline({
    intakeService: services.intakeService,
    entryRepo: repos.entryRepo,
    fingerprintRepo: repos.fingerprintRepo,
    mappingRuleRepo: repos.mappingRuleRepo,
    auditService: services.auditService
  });

  return { db, repos, pipeline };
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("e2e-ingest-") && file.endsWith(".sqlite")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("E2E receipt + statement ingestion", () => {
  it("normalizes both source types into the same canonical schema with audit history", async () => {
    const { db, pipeline, repos } = setup();

    repos.mappingRuleRepo.upsert({
      ruleId: "rule_spotify",
      field: "merchant",
      pattern: "SM SUPERMARKET",
      targetCategory: "groceries",
      priority: 10,
      createdBy: "system",
      createdAt: "2026-04-17T00:00:00+00:00"
    });

    const receiptEntries = await pipeline.run(path.resolve("src/fixtures/receipts/receipt-text.txt"), "receipt_text");
    const statementEntries = await pipeline.run(path.resolve("src/fixtures/statements/bank-sample.csv"), "bank_statement");

    expect(receiptEntries.length).toBeGreaterThanOrEqual(1);
    expect(statementEntries.length).toBeGreaterThanOrEqual(1);

    const all = repos.entryRepo.listAll();
    expect(all.length).toBe(receiptEntries.length + statementEntries.length);
    expect(all.every((entry) => typeof entry.entryId === "string" && entry.entryId.length > 0)).toBe(true);
    expect(all.every((entry) => entry.sourceDocument.documentId.length > 0)).toBe(true);
    expect(all.every((entry) => entry.extractionMeta.extractorVersion === "v1")).toBe(true);
    expect(all.some((entry) => entry.sourceDocument.sourceType === "receipt")).toBe(true);
    expect(all.some((entry) => entry.sourceDocument.sourceType === "bank_statement")).toBe(true);

    const auditRows = repos.auditRepo.listByEntryId(all[0]?.entryId ?? "");
    expect(auditRows.length).toBeGreaterThan(0);

    db.close();
  });
});
