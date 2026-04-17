import type { ReceiptCandidate, ReceiptTextInput } from "./receipt-text-port.js";

const DATE_REGEXES = [
  /\b(\d{4}-\d{2}-\d{2})\b/,
  /\b(\d{2}\/\d{2}\/\d{4})\b/,
  /\b(\d{2}-\d{2}-\d{4})\b/
];

const CURRENCY_REGEX = /\b(PHP|USD|EUR)\b/i;
const TOTAL_REGEX = /(?:total|amount due|grand total)\s*[:\-]?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i;
const TAX_REGEX = /(?:tax|vat)\s*[:\-]?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i;

function parseMerchant(text: string): string | undefined {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  return lines[0];
}

function findFirstMatch(text: string, regexes: RegExp[]): string | undefined {
  for (const regex of regexes) {
    const match = text.match(regex);
    if (match?.[1]) {
      return match[1];
    }
  }
  return undefined;
}

export function adaptReceiptText(input: ReceiptTextInput): ReceiptCandidate {
  const text = input.text.trim();
  const merchantRaw = parseMerchant(text);
  const transactionDateRaw = findFirstMatch(text, DATE_REGEXES);
  const amountRaw = text.match(TOTAL_REGEX)?.[1];
  const taxAmountRaw = text.match(TAX_REGEX)?.[1];
  const currencyRaw = text.match(CURRENCY_REGEX)?.[1]?.toUpperCase() ?? input.currencyHint;

  let confidence = 0.2;
  const warnings: string[] = [];

  if (merchantRaw) confidence += 0.2;
  else warnings.push("merchant_missing");

  if (transactionDateRaw) confidence += 0.2;
  else warnings.push("date_missing");

  if (amountRaw) confidence += 0.3;
  else warnings.push("amount_missing");

  if (currencyRaw) confidence += 0.1;
  else warnings.push("currency_missing");

  const lineItems = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /[0-9]/.test(line) && line.length < 120)
    .slice(0, 8)
    .map((line) => ({ description: line }));

  return {
    merchantRaw,
    transactionDateRaw,
    amountRaw,
    currencyRaw,
    taxAmountRaw,
    lineItems,
    confidence: Math.min(1, confidence),
    warnings,
    rawText: text
  };
}
