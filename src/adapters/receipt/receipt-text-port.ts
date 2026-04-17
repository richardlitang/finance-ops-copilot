export type ReceiptTextInput = {
  text: string;
  filename?: string;
  localeHint?: string;
  currencyHint?: string;
};

export type ReceiptLineItem = {
  description: string;
  amount?: number;
};

export type ReceiptCandidate = {
  merchantRaw?: string;
  transactionDateRaw?: string;
  amountRaw?: string;
  currencyRaw?: string;
  taxAmountRaw?: string;
  lineItems: ReceiptLineItem[];
  confidence: number;
  warnings: string[];
  rawText: string;
};
