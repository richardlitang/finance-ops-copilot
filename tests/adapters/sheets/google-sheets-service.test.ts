import { describe, expect, it } from "vitest";
import { GoogleSheetsService, type SheetsGateway } from "../../../src/adapters/sheets/google-sheets-service.js";
import type { NormalizedEntry } from "../../../src/domain/schemas.js";

class InMemoryGateway implements SheetsGateway {
  public writes: Array<{ tab: string; rows: Array<Record<string, unknown>>; keyField: string }> = [];
  async upsertRows(tab: string, rows: Array<Record<string, unknown>>, keyField: string): Promise<void> {
    this.writes.push({ tab, rows, keyField });
  }
}

function buildEntry(partial: Partial<NormalizedEntry>): NormalizedEntry {
  const now = "2026-04-17T00:00:00+00:00";
  return {
    entryId: partial.entryId ?? "entry_1",
    sourceDocument: partial.sourceDocument ?? {
      documentId: "doc_1",
      sourceType: "bank_statement",
      filename: "sample.csv",
      mimeType: "text/csv",
      importedAt: now
    },
    amount: partial.amount ?? 100,
    currency: partial.currency ?? "USD",
    categoryDecision: partial.categoryDecision ?? {
      suggestedCategory: "shopping",
      confidence: 0.9,
      source: "rule"
    },
    duplicateCheck: partial.duplicateCheck ?? { status: "none", confidence: 0.1, signals: [] },
    status: partial.status ?? "approved",
    reviewReasons: partial.reviewReasons ?? [],
    extractionMeta: partial.extractionMeta ?? { extractorVersion: "v1", confidence: 0.9, warnings: [] },
    lineItems: partial.lineItems ?? [],
    createdAt: partial.createdAt ?? now,
    updatedAt: partial.updatedAt ?? now,
    merchantRaw: partial.merchantRaw,
    merchantNormalized: partial.merchantNormalized,
    description: partial.description,
    reference: partial.reference,
    transactionDate: partial.transactionDate,
    postingDate: partial.postingDate,
    baseAmount: partial.baseAmount,
    baseCurrency: partial.baseCurrency,
    taxAmount: partial.taxAmount
  };
}

describe("GoogleSheetsService", () => {
  it("syncs only approved non-exact-duplicate entries", async () => {
    const gateway = new InMemoryGateway();
    const service = new GoogleSheetsService(gateway);
    const count = await service.syncApprovedEntries([
      buildEntry({ entryId: "a", status: "approved" }),
      buildEntry({ entryId: "b", status: "needs_review" }),
      buildEntry({
        entryId: "c",
        status: "approved",
        duplicateCheck: { status: "exact_duplicate_import", confidence: 1, signals: [] }
      })
    ]);

    expect(count).toBe(1);
    expect(gateway.writes[0]?.tab).toBe("normalized_entries");
  });
});
