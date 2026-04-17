import { describe, expect, it } from "vitest";
import { evaluateReviewPolicy, type ReviewPolicyInput } from "../../src/domain/review-policy.js";

const baseInput: ReviewPolicyInput = {
  amount: 100,
  currency: "USD",
  transactionDate: "2026-04-16",
  extractionMeta: {
    extractorVersion: "v1",
    confidence: 0.9,
    warnings: []
  },
  categoryDecision: {
    suggestedCategory: "shopping",
    confidence: 0.9,
    source: "rule" as const
  },
  duplicateCheck: {
    status: "none" as const,
    confidence: 0.1,
    signals: []
  }
};

describe("evaluateReviewPolicy", () => {
  it("returns normalized for valid and low-risk input", () => {
    const result = evaluateReviewPolicy(baseInput);
    expect(result.status).toBe("normalized");
    expect(result.reviewReasons).toEqual([]);
  });

  it("routes low confidence entries to review", () => {
    const result = evaluateReviewPolicy({
      ...baseInput,
      extractionMeta: {
        ...baseInput.extractionMeta,
        confidence: 0.4
      }
    });

    expect(result.status).toBe("needs_review");
    expect(result.reviewReasons).toContain("low_extraction_confidence");
  });

  it("routes duplicate suspects to review", () => {
    const result = evaluateReviewPolicy({
      ...baseInput,
      duplicateCheck: {
        status: "near_duplicate_suspected",
        confidence: 0.8,
        signals: ["same_amount"]
      }
    });

    expect(result.status).toBe("needs_review");
    expect(result.reviewReasons).toContain("duplicate_suspected");
  });

  it("supports explicit auto-approval for safe entries", () => {
    const result = evaluateReviewPolicy({
      ...baseInput,
      allowLowRiskAutoApprove: true
    });

    expect(result.status).toBe("approved");
    expect(result.reviewReasons).toEqual([]);
  });
});
