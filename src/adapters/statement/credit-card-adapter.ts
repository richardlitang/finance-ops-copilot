import { parseCsv } from "./csv-parser.js";
import { CREDIT_CARD_HEADER_ALIASES } from "./profiles.js";
import type { StatementCandidateRow } from "./types.js";

type CardAdapterOptions = {
  accountHint?: string;
  currencyHint?: string;
};

function pick(row: Record<string, string>, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = row[key];
    if (value && value.trim() !== "") {
      return value.trim();
    }
  }
  return undefined;
}

function amountForCardRow(row: Record<string, string>): string | undefined {
  const raw = pick(row, ["amount", "transaction_amount"]);
  if (raw) {
    return raw;
  }
  const debit = Number((pick(row, ["debit", "charges"]) ?? "0").replace(/[,\s]/g, ""));
  const credit = Number((pick(row, ["credit", "payments"]) ?? "0").replace(/[,\s]/g, ""));
  if (!Number.isNaN(debit) || !Number.isNaN(credit)) {
    return String(debit - credit);
  }
  return undefined;
}

export function adaptCreditCardCsv(content: string, options?: CardAdapterOptions): StatementCandidateRow[] {
  const parsed = parseCsv(content, {
    headerAliases: CREDIT_CARD_HEADER_ALIASES
  });
  return parsed.rows.map((row) => ({
    source: "credit_card_statement",
    transactionDateRaw: pick(row, ["transaction_date", "date", "trans_date"]),
    postingDateRaw: pick(row, ["posting_date", "posted_date"]),
    merchantRaw: pick(row, ["merchant", "merchant_name"]),
    descriptionRaw: pick(row, ["description", "details"]),
    referenceRaw: pick(row, ["reference", "reference_number", "auth_code"]),
    amountRaw: amountForCardRow(row),
    currencyRaw: pick(row, ["currency"]) ?? options?.currencyHint,
    accountHint: options?.accountHint,
    confidence: 0.9,
    warnings: [],
    rawText: JSON.stringify(row),
    rawRow: row
  }));
}
