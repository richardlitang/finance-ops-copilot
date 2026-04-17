import type { DuplicateCheckResult, NormalizedEntry } from "../domain/schemas.js";

export type DuplicateCandidate = Pick<
  NormalizedEntry,
  "entryId" | "amount" | "merchantNormalized" | "transactionDate" | "description"
> & { importFingerprint?: string };

type DuplicateEngineInput = {
  candidate: DuplicateCandidate & { importFingerprint?: string };
  existing: DuplicateCandidate[];
  knownFingerprints: Map<string, string>;
};

function dayDiff(a: string | undefined, b: string | undefined): number | null {
  if (!a || !b) return null;
  const d1 = new Date(`${a}T00:00:00Z`).getTime();
  const d2 = new Date(`${b}T00:00:00Z`).getTime();
  if (Number.isNaN(d1) || Number.isNaN(d2)) return null;
  return Math.abs(Math.round((d1 - d2) / (1000 * 60 * 60 * 24)));
}

function similarDescription(a?: string, b?: string): boolean {
  if (!a || !b) return false;
  const left = a.toLowerCase();
  const right = b.toLowerCase();
  return left.includes(right.slice(0, Math.min(right.length, 10))) || right.includes(left.slice(0, Math.min(left.length, 10)));
}

export function evaluateDuplicate(input: DuplicateEngineInput): DuplicateCheckResult {
  if (input.candidate.importFingerprint) {
    const existingEntryId = input.knownFingerprints.get(input.candidate.importFingerprint);
    if (existingEntryId) {
      return {
        status: "exact_duplicate_import",
        confidence: 1,
        relatedEntryId: existingEntryId,
        signals: ["import_fingerprint_match"]
      };
    }
  }

  let bestNear: { score: number; entryId: string; signals: string[]; dayDistance: number | null } | undefined;
  let recurringHit: { entryId: string; signals: string[] } | undefined;

  for (const existing of input.existing) {
    const signals: string[] = [];
    let score = 0;

    if (existing.amount === input.candidate.amount) {
      score += 0.45;
      signals.push("same_amount");
    }
    if (existing.merchantNormalized && existing.merchantNormalized === input.candidate.merchantNormalized) {
      score += 0.3;
      signals.push("same_merchant");
    }

    const distance = dayDiff(existing.transactionDate, input.candidate.transactionDate);
    if (distance !== null && distance <= 3) {
      score += 0.2;
      signals.push("date_within_3_days");
    }
    if (similarDescription(existing.description, input.candidate.description)) {
      score += 0.1;
      signals.push("similar_description");
    }

    if (distance !== null && distance >= 25 && distance <= 40 && signals.includes("same_amount") && signals.includes("same_merchant")) {
      recurringHit = { entryId: existing.entryId, signals: ["monthly_pattern", "same_amount", "same_merchant"] };
    }

    if (!bestNear || score > bestNear.score) {
      bestNear = { score, entryId: existing.entryId, signals, dayDistance: distance };
    }
  }

  if (bestNear && bestNear.score >= 0.75 && bestNear.signals.includes("date_within_3_days")) {
    return {
      status: "near_duplicate_suspected",
      confidence: Math.min(1, bestNear.score),
      relatedEntryId: bestNear.entryId,
      signals: bestNear.signals
    };
  }

  if (recurringHit) {
    return {
      status: "recurring_candidate",
      confidence: 0.8,
      relatedEntryId: recurringHit.entryId,
      signals: recurringHit.signals
    };
  }

  return {
    status: "none",
    confidence: 0.05,
    signals: []
  };
}
