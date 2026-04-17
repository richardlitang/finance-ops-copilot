import type { CategoryDecision, DuplicateCheckResult, ExtractionMeta } from "./schemas.js";
import type { EntryStatus, ReviewReason } from "./enums.js";

export type ReviewPolicyInput = {
  amount?: number;
  currency?: string;
  transactionDate?: string;
  extractionMeta: ExtractionMeta;
  categoryDecision: CategoryDecision;
  duplicateCheck: DuplicateCheckResult;
  allowLowRiskAutoApprove?: boolean;
};

export type ReviewPolicyResult = {
  status: EntryStatus;
  reviewReasons: ReviewReason[];
};

const EXTRACTION_CONFIDENCE_THRESHOLD = 0.7;
const CATEGORY_CONFIDENCE_THRESHOLD = 0.6;

export function evaluateReviewPolicy(input: ReviewPolicyInput): ReviewPolicyResult {
  const reviewReasons = new Set<ReviewReason>();

  if (typeof input.amount !== "number" || Number.isNaN(input.amount)) {
    reviewReasons.add("missing_amount");
  }
  if (!input.currency) {
    reviewReasons.add("missing_currency");
  }
  if (!input.transactionDate) {
    reviewReasons.add("missing_transaction_date");
  }

  if (input.extractionMeta.confidence < EXTRACTION_CONFIDENCE_THRESHOLD) {
    reviewReasons.add("low_extraction_confidence");
  }

  if (input.categoryDecision.confidence < CATEGORY_CONFIDENCE_THRESHOLD) {
    reviewReasons.add("uncertain_category");
  }

  if (input.duplicateCheck.status === "exact_duplicate_import") {
    reviewReasons.add("exact_duplicate_import");
  } else if (input.duplicateCheck.status === "near_duplicate_suspected") {
    reviewReasons.add("duplicate_suspected");
  }

  const finalizedReasons = [...reviewReasons];
  if (finalizedReasons.length > 0) {
    return {
      status: "needs_review",
      reviewReasons: finalizedReasons
    };
  }

  if (input.allowLowRiskAutoApprove) {
    return {
      status: "approved",
      reviewReasons: []
    };
  }

  return {
    status: "normalized",
    reviewReasons: []
  };
}
