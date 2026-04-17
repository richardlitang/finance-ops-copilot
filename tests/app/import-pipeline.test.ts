import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { DocumentRepo } from "../../src/infra/db/document-repo.js";
import { EntryRepo } from "../../src/infra/db/entry-repo.js";
import { MappingRuleRepo } from "../../src/infra/db/mapping-rule-repo.js";
import { AuditRepo } from "../../src/infra/db/audit-repo.js";
import { FingerprintRepo } from "../../src/infra/db/fingerprint-repo.js";
import { ExtractedCandidateRepo } from "../../src/infra/db/extracted-candidate-repo.js";
import { IntakeService } from "../../src/app/intake-service.js";
import { AuditService } from "../../src/app/audit-service.js";
import { ImportPipeline } from "../../src/app/import-pipeline.js";
import type { OcrPort } from "../../src/adapters/receipt/ocr-port.js";
import { cleanupTempDatabases, createMigratedTestDatabase } from "../helpers/test-db.js";

function setup() {
  const { db } = createMigratedTestDatabase("pipeline");
  const repos = {
    documentRepo: new DocumentRepo(db),
    entryRepo: new EntryRepo(db),
    mappingRuleRepo: new MappingRuleRepo(db),
    auditRepo: new AuditRepo(db),
    fingerprintRepo: new FingerprintRepo(db),
    extractedCandidateRepo: new ExtractedCandidateRepo(db)
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
    extractedCandidateRepo: repos.extractedCandidateRepo,
    auditService: services.auditService
  });
  return { db, repos, services, pipeline };
}

afterEach(() => {
  cleanupTempDatabases("pipeline");
});

describe("ImportPipeline", () => {
  it("imports a statement file and persists entries with review-safe status", async () => {
    const { db, pipeline, repos } = setup();
    repos.mappingRuleRepo.upsert({
      ruleId: "rule_1",
      field: "merchant",
      pattern: "SM SUPERMARKET",
      targetCategory: "groceries",
      priority: 10,
      createdBy: "system",
      createdAt: "2026-04-17T00:00:00+00:00"
    });
    repos.mappingRuleRepo.upsert({
      ruleId: "rule_1_desc",
      field: "description",
      pattern: "SM SUPERMARKET",
      targetCategory: "groceries",
      priority: 9,
      createdBy: "system",
      createdAt: "2026-04-17T00:00:00+00:00"
    });
    repos.mappingRuleRepo.upsert({
      ruleId: "rule_2_desc",
      field: "description",
      pattern: "FREELANCE CLIENT",
      targetCategory: "income",
      priority: 9,
      createdBy: "system",
      createdAt: "2026-04-17T00:00:00+00:00"
    });

    const first = await pipeline.run(path.resolve("src/fixtures/statements/bank-sample.csv"), "bank_statement");
    expect(first.length).toBe(2);
    expect(first.every((entry) => entry.status === "normalized")).toBe(true);

    const second = await pipeline.run(path.resolve("src/fixtures/statements/bank-sample.csv"), "bank_statement");
    expect(second.some((entry) => entry.duplicateCheck.status === "exact_duplicate_import")).toBe(true);
    const candidates = repos.extractedCandidateRepo.listByDocumentId(first[0]!.sourceDocument.documentId);
    expect(candidates).toHaveLength(2);
    expect(candidates.every((candidate) => candidate.entryId !== undefined)).toBe(true);

    db.close();
  });

  it("routes image receipts through OCR adapter when provided", async () => {
    const { db, repos, services } = setup();
    class FakeOcrPort implements OcrPort {
      async extractTextFromImage(): Promise<string> {
        return "SM SUPERMARKET\nDate: 04/16/2026\nTotal: 420.50 PHP";
      }
    }

    const pipeline = new ImportPipeline({
      intakeService: services.intakeService,
      entryRepo: repos.entryRepo,
      fingerprintRepo: repos.fingerprintRepo,
      mappingRuleRepo: repos.mappingRuleRepo,
      extractedCandidateRepo: repos.extractedCandidateRepo,
      auditService: services.auditService,
      ocrPort: new FakeOcrPort()
    });

    const imagePath = path.resolve(".tmp/receipt-image-test.jpg");
    fs.writeFileSync(imagePath, Buffer.from([0xff, 0xd8, 0xff, 0xd9]));

    const entries = await pipeline.run(imagePath, "receipt");
    expect(entries).toHaveLength(1);
    expect(entries[0]?.currency).toBe("PHP");
    expect(entries[0]?.amount).toBe(420.5);
    const candidates = repos.extractedCandidateRepo.listByEntryId(entries[0]!.entryId);
    expect(candidates[0]?.rawText).toContain("SM SUPERMARKET");

    fs.rmSync(imagePath, { force: true });
    db.close();
  });
});
