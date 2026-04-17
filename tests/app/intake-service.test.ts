import { afterEach, describe, expect, it } from "vitest";
import { DocumentRepo } from "../../src/infra/db/document-repo.js";
import { IntakeService } from "../../src/app/intake-service.js";
import { cleanupTempDatabases, createMigratedTestDatabase } from "../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("intake");
});

describe("IntakeService", () => {
  it("records imported document metadata and hints", () => {
    const { db } = createMigratedTestDatabase("intake");
    const repo = new DocumentRepo(db);
    const service = new IntakeService(repo);

    const result = service.createIntake({
      filename: "statement.csv",
      mimeType: "text/csv",
      sourceType: "bank_statement",
      sourceHint: "unionbank",
      localeHint: "en-PH",
      countryHint: "PH",
      rawText: "date,amount,merchant"
    });

    expect(result.document.documentId.length).toBeGreaterThan(0);
    expect(result.document.sourceType).toBe("bank_statement");
    expect(result.document.localeHint).toBe("en-PH");
    db.close();
  });
});
