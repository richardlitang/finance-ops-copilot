import { parseCsv } from "./csv-parser.js";
import { BANK_STATEMENT_HEADER_ALIASES } from "./profiles.js";
import type { StatementCandidateRow } from "./types.js";

type BankAdapterOptions = {
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

function getAmount(row: Record<string, string>): string | undefined {
  const amount = pick(row, ["amount", "transaction_amount"]);
  if (amount) {
    return amount;
  }

  const debit = Number((pick(row, ["debit", "withdrawal"]) ?? "0").replace(/[,\s]/g, ""));
  const credit = Number((pick(row, ["credit", "deposit"]) ?? "0").replace(/[,\s]/g, ""));
  if (!Number.isNaN(debit) || !Number.isNaN(credit)) {
    return String(credit - debit);
  }
  return undefined;
}

export function adaptBankStatementCsv(content: string, options?: BankAdapterOptions): StatementCandidateRow[] {
  const parsed = parseCsv(content, {
    headerAliases: BANK_STATEMENT_HEADER_ALIASES
  });
  return parsed.rows.map((row) => ({
    source: "bank_statement",
    transactionDateRaw: pick(row, ["date", "transaction_date", "value_date"]),
    postingDateRaw: pick(row, ["posting_date", "book_date"]),
    merchantRaw: pick(row, ["merchant", "payee", "beneficiary"]),
    descriptionRaw: pick(row, ["description", "details", "memo", "narrative"]),
    referenceRaw: pick(row, ["reference", "ref", "transaction_id"]),
    amountRaw: getAmount(row),
    currencyRaw: pick(row, ["currency"]) ?? options?.currencyHint,
    accountHint: options?.accountHint,
    confidence: 0.9,
    warnings: [],
    rawText: JSON.stringify(row),
    rawRow: row
  }));
}
