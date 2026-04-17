import { describe, expect, it } from "vitest";
import { buildMonthlySummary } from "../../src/app/monthly-summary-service.js";
import type { NormalizedEntry } from "../../src/domain/schemas.js";

function entry(overrides: Partial<NormalizedEntry>): NormalizedEntry {
  const now = "2026-04-17T00:00:00+00:00";
  return {
    entryId: overrides.entryId ?? "entry_1",
    sourceDocument: overrides.sourceDocument ?? {
      documentId: "doc_1",
      sourceType: "bank_statement",
      filename: "sample.csv",
      mimeType: "text/csv",
      importedAt: now
    },
    amount: overrides.amount ?? 100,
    currency: overrides.currency ?? "USD",
    categoryDecision: overrides.categoryDecision ?? {
      suggestedCategory: "shopping",
      finalCategory: "shopping",
      confidence: 0.9,
      source: "rule"
    },
    duplicateCheck: overrides.duplicateCheck ?? { status: "none", confidence: 0.1, signals: [] },
    status: overrides.status ?? "approved",
    reviewReasons: overrides.reviewReasons ?? [],
    extractionMeta: overrides.extractionMeta ?? { extractorVersion: "v1", confidence: 0.9, warnings: [] },
    lineItems: overrides.lineItems ?? [],
    createdAt: overrides.createdAt ?? now,
    updatedAt: overrides.updatedAt ?? now,
    transactionDate: overrides.transactionDate ?? "2026-04-16",
    merchantRaw: overrides.merchantRaw ?? "merchant",
    merchantNormalized: overrides.merchantNormalized ?? "merchant",
    description: overrides.description,
    reference: overrides.reference,
    postingDate: overrides.postingDate,
    baseAmount: overrides.baseAmount,
    baseCurrency: overrides.baseCurrency,
    taxAmount: overrides.taxAmount
  };
}

describe("buildMonthlySummary", () => {
  it("aggregates category, merchant, and currency totals", () => {
    const rows = buildMonthlySummary([
      entry({ amount: 100, categoryDecision: { suggestedCategory: "shopping", finalCategory: "shopping", confidence: 0.9, source: "rule" } }),
      entry({ entryId: "entry_2", amount: 50, categoryDecision: { suggestedCategory: "shopping", finalCategory: "shopping", confidence: 0.8, source: "rule" } }),
      entry({ entryId: "entry_3", amount: 9.99, duplicateCheck: { status: "recurring_candidate", confidence: 0.8, signals: [] } })
    ]);

    expect(rows.some((row) => row.metric_type === "category_total")).toBe(true);
    expect(rows.some((row) => row.metric_type === "recurring_candidate")).toBe(true);
  });
});
