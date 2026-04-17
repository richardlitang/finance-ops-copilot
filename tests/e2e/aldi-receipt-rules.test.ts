import { afterEach, describe, expect, it } from "vitest";
import { createRuntime } from "../../src/cli/runtime.js";
import { importMappingRulesFromCsv } from "../../src/app/mapping-rule-importer.js";
import { cleanupTempDatabases, createMigratedTestDatabase } from "../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("aldi-receipt");
});

describe("E2E Aldi receipt with default rules", () => {
  it("classifies Aldi receipt text as groceries without review", async () => {
    const { dbPath } = createMigratedTestDatabase("aldi-receipt");
    const runtime = createRuntime({
      dbPath,
      env: {
        GOOGLE_SHEETS_ENABLED: "false"
      }
    });

    try {
      importMappingRulesFromCsv(
        "src/fixtures/mapping-rules/default-mapping-rules.csv",
        runtime.repos.mappingRuleRepo,
        {
          defaultCreatedBy: "system",
          nowIso: "2026-04-17T00:00:00+00:00"
        }
      );

      const entries = await runtime.services.importPipeline.run(
        "src/fixtures/receipts/aldi-text.txt",
        "receipt_text"
      );

      expect(entries).toHaveLength(1);
      expect(entries[0]?.merchantNormalized).toBe("aldi");
      expect(entries[0]?.amount).toBe(42.97);
      expect(entries[0]?.currency).toBe("EUR");
      expect(entries[0]?.transactionDate).toBe("2026-04-17");
      expect(entries[0]?.categoryDecision.finalCategory).toBe("groceries");
      expect(entries[0]?.status).toBe("normalized");
      expect(entries[0]?.reviewReasons).toEqual([]);
    } finally {
      runtime.db.close();
    }
  });
});
