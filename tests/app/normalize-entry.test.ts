import { describe, expect, it } from "vitest";
import { normalizeEntry } from "../../src/app/normalize-entry.js";

describe("normalizeEntry", () => {
  it("normalizes date, merchant, amount, and currency", () => {
    const entry = normalizeEntry({
      entryId: "entry_1",
      sourceDocument: {
        documentId: "doc_1",
        sourceType: "receipt",
        filename: "r.jpg",
        mimeType: "image/jpeg",
        importedAt: "2026-04-17T00:00:00+00:00"
      },
      candidate: {
        merchantRaw: "  SM   SUPERMARKET ",
        transactionDateRaw: "04/16/2026",
        amountRaw: "420.50",
        currencyRaw: "php"
      },
      extractionMeta: {
        extractorVersion: "v1",
        confidence: 0.9,
        warnings: []
      },
      categoryDecision: {
        suggestedCategory: "groceries",
        confidence: 0.9,
        source: "rule"
      },
      duplicateCheck: {
        status: "none",
        confidence: 0.1,
        signals: []
      },
      status: "normalized",
      reviewReasons: []
    });

    expect(entry.merchantNormalized).toBe("sm supermarket");
    expect(entry.transactionDate).toBe("2026-04-16");
    expect(entry.amount).toBe(420.5);
    expect(entry.currency).toBe("PHP");
  });

  it("parses decimal comma amounts", () => {
    const entry = normalizeEntry({
      entryId: "entry_2",
      sourceDocument: {
        documentId: "doc_2",
        sourceType: "receipt",
        filename: "r2.txt",
        mimeType: "text/plain",
        importedAt: "2026-04-17T00:00:00+00:00"
      },
      candidate: {
        merchantRaw: "ALDI",
        transactionDateRaw: "17/04/2026",
        amountRaw: "42,97",
        currencyRaw: "eur",
        taxAmountRaw: "2,43"
      },
      extractionMeta: {
        extractorVersion: "v1",
        confidence: 0.9,
        warnings: []
      },
      categoryDecision: {
        suggestedCategory: "shopping",
        confidence: 0.7,
        source: "rule"
      },
      duplicateCheck: {
        status: "none",
        confidence: 0.1,
        signals: []
      },
      status: "normalized",
      reviewReasons: []
    });

    expect(entry.transactionDate).toBe("2026-04-17");
    expect(entry.amount).toBe(42.97);
    expect(entry.taxAmount).toBe(2.43);
    expect(entry.currency).toBe("EUR");
  });
});
