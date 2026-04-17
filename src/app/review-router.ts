import { evaluateReviewPolicy } from "../domain/review-policy.js";
import type { NormalizedEntry } from "../domain/schemas.js";

type ReviewRouterInput = Pick<
  NormalizedEntry,
  "amount" | "currency" | "transactionDate" | "extractionMeta" | "categoryDecision" | "duplicateCheck"
> & { allowLowRiskAutoApprove?: boolean };

export function routeReview(input: ReviewRouterInput): Pick<NormalizedEntry, "status" | "reviewReasons"> {
  const result = evaluateReviewPolicy({
    amount: input.amount,
    currency: input.currency,
    transactionDate: input.transactionDate,
    extractionMeta: input.extractionMeta,
    categoryDecision: input.categoryDecision,
    duplicateCheck: input.duplicateCheck,
    allowLowRiskAutoApprove: input.allowLowRiskAutoApprove
  });

  const reasons = new Set(result.reviewReasons);
  if (input.extractionMeta.warnings.some((warning) => warning.toLowerCase().includes("parse"))) {
    reasons.add("parse_error");
  }

  if (input.extractionMeta.warnings.some((warning) => warning.toLowerCase().includes("ambiguous"))) {
    reasons.add("ambiguous_match");
  }

  if (reasons.size > 0) {
    return {
      status: "needs_review",
      reviewReasons: [...reasons]
    };
  }

  return result;
}
