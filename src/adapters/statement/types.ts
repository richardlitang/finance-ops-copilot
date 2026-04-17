export type StatementCandidateRow = {
  source: "bank_statement" | "credit_card_statement";
  transactionDateRaw?: string;
  postingDateRaw?: string;
  merchantRaw?: string;
  descriptionRaw?: string;
  referenceRaw?: string;
  amountRaw?: string;
  currencyRaw?: string;
  accountHint?: string;
  confidence?: number;
  warnings?: string[];
  rawText?: string;
  rawRow: Record<string, string>;
};
