import type { ReceiptCandidate, ReceiptLineItem, ReceiptTextInput } from "./receipt-text-port.js";

const DATE_REGEXES = [
  /\b(\d{4}-\d{2}-\d{2})\b/,
  /\b(\d{2}\/\d{2}\/\d{4})\b/,
  /\b(\d{2}-\d{2}-\d{4})\b/
];

const CURRENCY_REGEX = /\b(PHP|USD|EUR)\b/i;
const AMOUNT_PATTERN = "([0-9][0-9 .]*(?:[,.][0-9]{1,2})?)";
const TOTAL_REGEX = new RegExp(`(?:total|amount due|grand total|a payer)\\s*[:\\-]?\\s*${AMOUNT_PATTERN}`, "i");
const TAX_REGEX = new RegExp(`(?:tax|vat|tva)\\s*[:\\-]?\\s*${AMOUNT_PATTERN}`, "i");
const LINE_ITEM_AMOUNT_PATTERN = "-?(?:\\d+(?:[ .]\\d{3})*|\\d+)(?:[,.]\\d{2})";
const LINE_ITEM_REGEX = new RegExp(`^(.+?)\\s+(${LINE_ITEM_AMOUNT_PATTERN})\\s*(?:€|eur|php|usd)?$`, "i");
const NON_ITEM_PREFIX_REGEX =
  /^(?:total|amount due|grand total|a payer|date|payment|tva|vat|tax|client ticket|terminal|merchant|period|transaction|card|card sequence number|contactless|read method|authorization code|worldline|promo|vous venez d'economiser|merci pour votre achat)/i;

function parseLineAmount(raw: string): number | undefined {
  const trimmed = raw.trim();
  const hasComma = trimmed.includes(",");
  const hasDot = trimmed.includes(".");
  let cleaned = trimmed.replace(/\s/g, "");

  if (hasComma && hasDot) {
    if (trimmed.lastIndexOf(",") > trimmed.lastIndexOf(".")) {
      cleaned = cleaned.replace(/\./g, "").replace(",", ".");
    } else {
      cleaned = cleaned.replace(/,/g, "");
    }
  } else if (hasComma) {
    cleaned = cleaned.replace(",", ".");
  }

  const parsed = Number(cleaned);
  return Number.isNaN(parsed) ? undefined : parsed;
}

function shouldSkipItemLine(line: string): boolean {
  const normalized = line.trim();
  if (normalized.length === 0) {
    return true;
  }
  if (NON_ITEM_PREFIX_REGEX.test(normalized)) {
    return true;
  }
  if (/^\d+\s*x\s+/i.test(normalized)) {
    return true;
  }
  if (normalized.includes("%")) {
    return true;
  }
  return false;
}

function extractStructuredLineItems(text: string): ReceiptLineItem[] {
  const items: ReceiptLineItem[] = [];
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (shouldSkipItemLine(line)) {
      continue;
    }

    const match = line.match(LINE_ITEM_REGEX);
    if (!match?.[1]) {
      continue;
    }

    const description = match[1].trim();
    if (!description) {
      continue;
    }

    items.push({
      description,
      amount: match[2] ? parseLineAmount(match[2]) : undefined
    });
  }

  return items;
}

function extractFallbackLineItems(text: string): ReceiptLineItem[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /[0-9]/.test(line) && line.length < 120)
    .slice(0, 8)
    .map((line) => ({ description: line }));
}

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
      return match[1].trim();
    }
  }
  return undefined;
}

export function adaptReceiptText(input: ReceiptTextInput): ReceiptCandidate {
  const text = input.text.trim();
  const merchantRaw = parseMerchant(text);
  const transactionDateRaw = findFirstMatch(text, DATE_REGEXES);
  const amountRaw = text.match(TOTAL_REGEX)?.[1]?.trim();
  const taxAmountRaw = text.match(TAX_REGEX)?.[1]?.trim();
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

  const structuredLineItems = extractStructuredLineItems(text);
  const lineItems = structuredLineItems.length > 0 ? structuredLineItems : extractFallbackLineItems(text);

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
