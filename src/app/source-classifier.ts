import type { SourceType } from "../domain/enums.js";

export type SourceClassifierInput = {
  filename?: string;
  mimeType?: string;
  sourceHint?: string;
  rawText?: string;
  headers?: string[];
};

export type SourceClassifierResult = {
  sourceType: SourceType;
  confidence: number;
  rationale: string;
  usedFallback: boolean;
};

function includesAny(haystack: string, needles: string[]): boolean {
  const lower = haystack.toLowerCase();
  return needles.some((needle) => lower.includes(needle));
}

export function classifySource(input: SourceClassifierInput): SourceClassifierResult {
  const filename = input.filename?.toLowerCase() ?? "";
  const mimeType = input.mimeType?.toLowerCase() ?? "";
  const hint = input.sourceHint?.toLowerCase() ?? "";
  const headerBlob = (input.headers ?? []).join(" ").toLowerCase();
  const rawText = input.rawText?.toLowerCase() ?? "";

  if (includesAny(hint, ["receipt", "bank", "credit", "card"])) {
    if (hint.includes("receipt")) {
      return { sourceType: "receipt", confidence: 0.98, rationale: "explicit source hint", usedFallback: false };
    }
    if (hint.includes("credit") || hint.includes("card")) {
      return {
        sourceType: "credit_card_statement",
        confidence: 0.98,
        rationale: "explicit source hint",
        usedFallback: false
      };
    }
    return { sourceType: "bank_statement", confidence: 0.98, rationale: "explicit source hint", usedFallback: false };
  }

  if (includesAny(filename, ["receipt", "invoice"]) || mimeType.startsWith("image/")) {
    return { sourceType: "receipt", confidence: 0.9, rationale: "filename or mime type signal", usedFallback: false };
  }

  if (includesAny(filename, ["credit", "card", "visa", "mastercard", "amex"])) {
    return {
      sourceType: "credit_card_statement",
      confidence: 0.9,
      rationale: "filename card keyword signal",
      usedFallback: false
    };
  }

  if (includesAny(filename, ["bank", "statement", "checking", "savings"])) {
    return {
      sourceType: "bank_statement",
      confidence: 0.84,
      rationale: "filename statement keyword signal",
      usedFallback: false
    };
  }

  if (includesAny(headerBlob, ["card", "merchant", "posted date", "transaction date", "reference number"])) {
    return {
      sourceType: "credit_card_statement",
      confidence: 0.82,
      rationale: "statement headers look card-specific",
      usedFallback: false
    };
  }

  if (includesAny(headerBlob, ["balance", "withdrawal", "deposit", "account number", "running balance"])) {
    return {
      sourceType: "bank_statement",
      confidence: 0.82,
      rationale: "statement headers look bank-specific",
      usedFallback: false
    };
  }

  if (includesAny(rawText, ["total", "vat", "receipt no", "cashier"])) {
    return {
      sourceType: "receipt",
      confidence: 0.7,
      rationale: "receipt terms found in text",
      usedFallback: false
    };
  }

  return {
    sourceType: "bank_statement",
    confidence: 0.4,
    rationale: "ambiguous input, defaulting to bank statement",
    usedFallback: true
  };
}
