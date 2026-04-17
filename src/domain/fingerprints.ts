import { createHash } from "node:crypto";

export type ImportFingerprintInput = {
  institutionName?: string;
  accountSuffix?: string;
  rawDate?: string;
  rawDescription?: string;
  rawAmount?: string;
  rawReference?: string;
};

function normalizePart(value: string | undefined): string {
  if (!value) {
    return "";
  }
  return value.trim().replace(/\s+/g, " ").toLowerCase();
}

export function buildImportFingerprint(input: ImportFingerprintInput): string {
  const stable = [
    normalizePart(input.institutionName),
    normalizePart(input.accountSuffix),
    normalizePart(input.rawDate),
    normalizePart(input.rawDescription),
    normalizePart(input.rawAmount),
    normalizePart(input.rawReference)
  ].join("|");

  return createHash("sha256").update(stable).digest("hex");
}
