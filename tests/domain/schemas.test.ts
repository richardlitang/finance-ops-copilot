import { describe, expect, it } from "vitest";
import { normalizedEntrySchema } from "../../src/domain/schemas.js";

function buildValidEntry() {
  const now = "2026-04-17T00:00:00+00:00";
  return {
    entryId: "entry_1",
    sourceDocument: {
      documentId: "doc_1",
      sourceType: "bank_statement",
      filename: "bank.csv",
      mimeType: "text/csv",
      importedAt: now
    },
    merchantRaw: "SM SUPERMARKET",
    merchantNormalized: "sm supermarket",
    description: "Card purchase",
    transactionDate: "2026-04-16",
    postingDate: "2026-04-17",
    amount: 420.5,
    currency: "PHP",
    categoryDecision: {
      suggestedCategory: "groceries",
      confidence: 0.92,
      source: "rule",
      finalCategory: "groceries"
    },
    duplicateCheck: {
      status: "none",
      confidence: 0.03,
      signals: []
    },
    status: "normalized",
    reviewReasons: [],
    extractionMeta: {
      extractorVersion: "v1",
      confidence: 0.92,
      warnings: []
    },
    createdAt: now,
    updatedAt: now
  };
}

describe("normalizedEntrySchema", () => {
  it("accepts a valid normalized entry", () => {
    const parsed = normalizedEntrySchema.parse(buildValidEntry());
    expect(parsed.entryId).toBe("entry_1");
  });

  it("rejects missing required fields", () => {
    const invalid = buildValidEntry();
    // @ts-expect-error testing runtime schema behavior
    delete invalid.currency;

    const result = normalizedEntrySchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });

  it("rejects approved exact duplicate entries", () => {
    const invalid = {
      ...buildValidEntry(),
      status: "approved",
      duplicateCheck: {
        status: "exact_duplicate_import",
        confidence: 0.99,
        signals: ["same_source_fingerprint"]
      }
    };

    const result = normalizedEntrySchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });
});
