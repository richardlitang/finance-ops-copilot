import type { NormalizedEntry } from "../../domain/schemas.js";

export const SHEETS_TABS = [
  "raw_imports",
  "normalized_entries",
  "review_queue",
  "mapping_rules",
  "monthly_summary"
] as const;
export type SheetsTab = (typeof SHEETS_TABS)[number];

export type NormalizedEntryRow = {
  entry_id: string;
  source_type: string;
  document_id: string;
  merchant_name: string;
  transaction_date: string;
  posting_date: string;
  amount: number;
  currency: string;
  base_currency_amount: number | "";
  suggested_category: string;
  final_category: string;
  confidence: number;
  duplicate_status: string;
  status: string;
  review_reasons: string;
  export_timestamp: string;
};

export type ReviewQueueRow = {
  entry_id: string;
  issue_type: string;
  merchant: string;
  amount: number;
  currency: string;
  suggested_category: string;
  rationale: string;
  duplicate_signals: string;
  reviewer_status: string;
};

export type MonthlySummaryRow = {
  month: string;
  metric_type: "category_total" | "merchant_total" | "currency_total" | "recurring_candidate" | "uncategorized_count";
  metric_key: string;
  metric_value: number;
};

export function toNormalizedEntryRow(entry: NormalizedEntry, exportedAt: string): NormalizedEntryRow {
  return {
    entry_id: entry.entryId,
    source_type: entry.sourceDocument.sourceType,
    document_id: entry.sourceDocument.documentId,
    merchant_name: entry.merchantNormalized ?? entry.merchantRaw ?? "",
    transaction_date: entry.transactionDate ?? "",
    posting_date: entry.postingDate ?? "",
    amount: entry.amount,
    currency: entry.currency,
    base_currency_amount: entry.baseAmount ?? "",
    suggested_category: entry.categoryDecision.suggestedCategory,
    final_category: entry.categoryDecision.finalCategory ?? entry.categoryDecision.suggestedCategory,
    confidence: entry.categoryDecision.confidence,
    duplicate_status: entry.duplicateCheck.status,
    status: entry.status,
    review_reasons: entry.reviewReasons.join("|"),
    export_timestamp: exportedAt
  };
}

export function toReviewQueueRow(entry: NormalizedEntry): ReviewQueueRow {
  return {
    entry_id: entry.entryId,
    issue_type: entry.reviewReasons[0] ?? "needs_review",
    merchant: entry.merchantNormalized ?? entry.merchantRaw ?? "",
    amount: entry.amount,
    currency: entry.currency,
    suggested_category: entry.categoryDecision.suggestedCategory,
    rationale: entry.categoryDecision.rationale ?? "",
    duplicate_signals: entry.duplicateCheck.signals.join("|"),
    reviewer_status: entry.status
  };
}
