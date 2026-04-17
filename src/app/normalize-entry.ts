import type { CategoryDecision, DuplicateCheckResult, ExtractionMeta, NormalizedEntry } from "../domain/schemas.js";
import type { SourceDocumentRef } from "../domain/schemas.js";

type CandidateInput = {
  merchantRaw?: string;
  descriptionRaw?: string;
  referenceRaw?: string;
  transactionDateRaw?: string;
  postingDateRaw?: string;
  amountRaw?: string;
  currencyRaw?: string;
  taxAmountRaw?: string;
  lineItems?: Array<{ description: string; amount?: number }>;
};

type NormalizeInput = {
  entryId: string;
  sourceDocument: SourceDocumentRef;
  candidate: CandidateInput;
  extractionMeta: ExtractionMeta;
  categoryDecision: CategoryDecision;
  duplicateCheck: DuplicateCheckResult;
  status: NormalizedEntry["status"];
  reviewReasons: NormalizedEntry["reviewReasons"];
  nowIso?: string;
};

function normalizeMerchant(merchantRaw?: string): string | undefined {
  return merchantRaw?.trim().replace(/\s+/g, " ").toLowerCase();
}

function normalizeDate(value?: string): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;

  const slash = trimmed.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slash) {
    const month = slash[1];
    const day = slash[2];
    const year = slash[3];
    return `${year}-${month}-${day}`;
  }

  const dash = trimmed.match(/^(\d{2})-(\d{2})-(\d{4})$/);
  if (dash) {
    const month = dash[1];
    const day = dash[2];
    const year = dash[3];
    return `${year}-${month}-${day}`;
  }

  return undefined;
}

function parseAmount(raw?: string): number {
  if (!raw) {
    return Number.NaN;
  }
  const cleaned = raw.replace(/[,$\s]/g, "");
  const num = Number(cleaned);
  return Number.isNaN(num) ? Number.NaN : num;
}

function normalizeCurrency(raw?: string): string {
  return (raw ?? "").trim().toUpperCase();
}

export function normalizeEntry(input: NormalizeInput): NormalizedEntry {
  const now = input.nowIso ?? new Date().toISOString();
  const amount = parseAmount(input.candidate.amountRaw);
  const taxAmount = parseAmount(input.candidate.taxAmountRaw);

  return {
    entryId: input.entryId,
    sourceDocument: input.sourceDocument,
    merchantRaw: input.candidate.merchantRaw,
    merchantNormalized: normalizeMerchant(input.candidate.merchantRaw),
    description: input.candidate.descriptionRaw,
    reference: input.candidate.referenceRaw,
    transactionDate: normalizeDate(input.candidate.transactionDateRaw),
    postingDate: normalizeDate(input.candidate.postingDateRaw),
    amount,
    currency: normalizeCurrency(input.candidate.currencyRaw),
    taxAmount: Number.isNaN(taxAmount) ? undefined : taxAmount,
    lineItems: input.candidate.lineItems ?? [],
    categoryDecision: input.categoryDecision,
    duplicateCheck: input.duplicateCheck,
    status: input.status,
    reviewReasons: input.reviewReasons,
    extractionMeta: input.extractionMeta,
    createdAt: now,
    updatedAt: now
  };
}
